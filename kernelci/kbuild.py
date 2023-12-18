# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
"""
KernelCI kernel build abstraction package
Initial version, still work in progress
Roadmap:
- correct build status - fail/pass/incomplete
- Code deuglification
- Reuse API class/functions and other code from KernelCI
- Add support for multiple CPU architectures (arm64, arm, mips, etc)
- Add support for multiple compilers (clang)
- Implement 3-stage build process
  (fetch-prepare, build, package) with 3 containers
  (kernelci, compiler-specific, kernelci)
"""

import os
import sys
import re
import tarfile
import json
import requests
import yaml
import kernelci.api
import kernelci.api.helper
import kernelci.config
import kernelci.config.storage
import kernelci.storage


CROS_CONFIG_URL = \
    "https://chromium.googlesource.com/chromiumos/third_party/kernel/+archive/refs/heads/{branch}/chromeos/config.tar.gz"  # noqa
LEGACY_CONFIG = '/etc/kernelci/core/build-configs.yaml'
FW_GIT = "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git"  # noqa

# Hard-coded make targets for each CPU architecture
MAKE_TARGETS = {
    'arm': 'zImage',
    'arm64': 'Image',
    'arc': 'uImage',
    'i386': 'bzImage',
    'x86_64': 'bzImage',
    'mips': 'uImage.gz',
    'sparc': 'zImage',
}

# Hard-coded binary kernel image names for each CPU architecture
KERNEL_IMAGE_NAMES = {
    'arm': {'zImage', 'xipImage'},
    'arm64': {'Image'},
    'arc': {'uImage'},
    'i386': {'bzImage'},
    'mips': {'uImage.gz', 'vmlinux.gz.itb', 'vmlinuz'},
    'riscv': {'Image', 'Image.gz'},
    'sparc': {'zImage'},
    'x86_64': {'bzImage'},
    'x86': {'bzImage'},
}

ARTIFACT_NAMES = {
    'modules.tar.gz': 'modules',
    'modules.tar.xz': 'modules',
}


def _download_file(url, file_path):
    '''
    Download file to file_path
    TODO(nuclearcat): Do we have anything generic in KernelCI for this?
    '''
    print(f"[_download_file] Downloading {url} to {file_path}")
    r = requests.get(url, stream=True, timeout=60)
    if r.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
        return True
    return False


class KBuild():
    '''
    Build class that represents kernel build
    if node, jobname and params are provided, create new build object
    if jsonobj is provided, load class from serialized json
    '''
    def __init__(self, node=None, jobname=None, params=None, jsonobj=None):
        # create new build object
        if node and jobname and params:
            self._workspace = None
            self._arch = params['arch']
            self._compiler = params['compiler']
            self._defconfig = params['defconfig']
            self._fragments = params['fragments']
            self._apijobname = jobname
            self._steps = []
            self._artifacts = []
            self._current_job = None
            self._config_full = ''
            self._srctarball = node['artifacts']['tarball']
            self._srcdir = None
            self._firmware_dir = None
            self._af_dir = None
            self._node = node
            return
        # load class from serialized json
        if jsonobj:
            self._arch = jsonobj['arch']
            self._compiler = jsonobj['compiler']
            self._defconfig = jsonobj['defconfig']
            self._fragments = jsonobj['fragments']
            self._steps = jsonobj['steps']
            self._artifacts = jsonobj['artifacts']
            self._current_job = jsonobj['current_job']
            self._config_full = jsonobj['config_full']
            self._srcdir = jsonobj['srcdir']
            self._srctarball = jsonobj['srctarball']
            self._firmware_dir = jsonobj['firmware_dir']
            self._af_dir = jsonobj['af_dir']
            self._workspace = jsonobj['workspace']
            self._node = jsonobj['node']
            self._apijobname = jsonobj['apijobname']
            self._storage_config = jsonobj['storage_config']
            self._fragments_dir = jsonobj['fragments_dir']
            return
        raise ValueError("No valid arguments provided")

    @classmethod
    def from_json(cls, filename):
        """ Load class from json file """
        with open(filename, 'r') as f:
            data = json.load(f)
        # rename underscored fields
        datanew = {}
        for key in data:
            if key.startswith("_"):
                newkey = key[1:]
                datanew[newkey] = data[key]
            else:
                datanew[key] = data[key]
        return cls(jsonobj=datanew)

    def set_workspace(self, workspace):
        """ Set workspace directory.
        TODO: Add workspace creation if it doesn't exist to shell script
        """
        if not os.path.exists(workspace):
            print(f"[_set_workspace] Creating workspace {workspace}")
            os.makedirs(workspace)
        self._workspace = workspace
        self._firmware_dir = os.path.join(self._workspace, "firmware")
        self._af_dir = os.path.join(self._workspace, "artifacts")
        self._srcdir = os.path.join(self._workspace, "linux")
        self.init_steps()

    def set_api_config(self, api_config):
        """ Set API config """
        self._api_config = api_config

    def set_storage_config(self, storage_config):
        """ Set storage config """
        self._storage_config = storage_config

    def init_steps(self):
        """ Initialize build steps """
        # make sure firmware, artifacts and fragments directories exist
        os.makedirs(self._firmware_dir, exist_ok=True)
        os.makedirs(self._af_dir, exist_ok=True)
        os.makedirs(self._srcdir, exist_ok=True)
        self._fragments_dir = os.path.join(self._af_dir, "fragments")
        os.makedirs(self._fragments_dir, exist_ok=True)
        # Add shell script header, assume bash
        self._steps.append("#!/bin/bash -e")
        # Add comments about build metadata
        self.addcomment("Build metadata:")
        self.addcomment("  arch: " + self._arch)
        self.addcomment("  compiler: " + self._compiler)
        self.addcomment("  defconfig: " + self._defconfig)
        self.addcomment("  fragments: " + str(self._fragments))
        self.addcomment("  src_tarball: " + self._srctarball)
        self.addcomment("  apijobname: " + self._apijobname)
        self.addspacer()
        # set environment variables
        self.addcomment("Set environment variables")
        self.addcmd("export ARCH=" + self._arch)
        # self.addcmd("export CROSS_COMPILE=" + self._compiler + "-")
        self.addcmd("export INSTALL_MOD_PATH=_modules_")
        self.addcmd("export INSTALL_MOD_STRIP=1")
        # set -x for echo
        self._steps.append("set -x")
        # touch build.log
        self.addcmd("touch " + self._af_dir + "/build.log")
        self.addcmd("tail -f " + self._af_dir + "/build.log &")
        self.addcmd("tailpid=$!")
        # artifacts/build.log
        self.addcmd(f"exec >>{self._af_dir}/build.log 2>&1")
        # same time add tail and fork, so i see build.log in real time
        # but keep pid, so i can kill it later
        self._artifacts.append("build.log")
        self._artifacts.append("build_kimage.log")
        self._artifacts.append("build_kimage_stderr.log")
        self._artifacts.append("build_modules.log")
        self._artifacts.append("build_modules_stderr.log")
        # download tarball
        self.addcomment("Download tarball")
        self.addcmd("cd " + self._workspace)
        self.addcmd("wget -c -t 10 \"" + self._srctarball + "\" -O linux.tgz")
        self.addcmd("tar -xzf linux.tgz -C " + self._srcdir + " --strip-components=1")  # noqa

    def addspacer(self):
        """ Add empty line, mostly for easier reading """
        self._steps.append("")

    def addcomment(self, comment):
        """ Add comment to script """
        self._steps.append("# " + comment)

    def startjob(self, jobname):
        """ Start new job, if jobname is empty, just finish previous job """
        # set previous job state file to complete
        # state is in artifacts/state.txt
        if self._current_job:
            self.addcomment("Finishing job " + self._current_job)
            cmd = f'echo job:{self._current_job}='
            cmd += f'done >> {self._af_dir}/state.txt'
            self._steps.append(cmd)
            # add timestamp
            cmd = f'echo jobets:{self._current_job}='
            cmd += f'$(date +%s) >> {self._af_dir}/state.txt'
            self._steps.append(cmd)
        self.addspacer()
        if not jobname:
            return
        self.addcomment("Starting job " + jobname)
        self._steps.append(f'echo -----log:{jobname}-----')
        self._current_job = jobname
        cmd = f'echo job:{jobname}=running >> {self._af_dir}/state.txt'  # noqa
        self._steps.append(cmd)
        cmd = f'echo jobsts:{jobname}=$(date +%s) >> {self._af_dir}/state.txt'  # noqa
        self._steps.append(cmd)

    def addcmd(self, cmd, critical=True):
        '''
        critical - if True, check return code and exit, as command is critical
        '''
        if not critical:
            cmd += " || true"
        self._steps.append(cmd)

    def _fetch_firmware(self):
        '''
        Fetch firmware from linux-firmware repo
        TODO: Implement caching and optional fetch
        TODO: Implement firmware commit id meta/settings
        '''
        self.startjob("fetch_firmware")
        self.addcmd(f"git clone {FW_GIT} --depth 1", False)
        self.addcmd("cd linux-firmware")
        self.addcmd("./copy-firmware.sh " + self._firmware_dir)
        self.addcmd("cd ..")
        # self.addcmd("rm -rf linux-firmware")

    def _getcrosfragment(self, fragment):
        """ Get ChromeOS specific configuration fragments """
        buffer = ''
        [(branch, config)] = re.findall(r"cros://([\w\-.]+)/(.*)", fragment)
        cros_config = "/tmp/cros-config.tgz"
        url = CROS_CONFIG_URL.format(branch=branch)
        if not _download_file(url, cros_config):
            raise FileNotFoundError(f"Error reading {url}")
        with tarfile.open(cros_config) as tar:
            subdir = 'chromeos'
            config_file_names = [
                os.path.join(subdir, 'base.config'),
                os.path.join(subdir, os.path.dirname(config), "common.config"),
                os.path.join(subdir, config),
            ]
            for file_name in config_file_names:
                buffer += tar.extractfile(file_name).read().decode('utf-8')

        os.unlink(cros_config)

        return buffer

    def extract_config(self, frag):
        """ Extract config fragments from legacy config file """
        txt = ''
        config = frag['configs']
        for c in config:
            txt += c + '\n'
        return txt

    def add_legacy_fragment(self, fragname):
        """ Add legacy config fragment from build-configs.yaml """
        buffer = ''
        with open(LEGACY_CONFIG, 'r') as cfgfile:
            content = cfgfile.read()
            yml = yaml.safe_load(content)

        print(f"Searching for fragment {fragname} in {LEGACY_CONFIG}")
        if 'fragments' in yml:
            frag = yml['fragments']
        else:
            print("No fragments section in config file")
            sys.exit(1)

        if fragname in frag:
            txt = self.extract_config(frag[fragname])
            buffer += txt
        else:
            print(f"Fragment {fragname} not found")
            sys.exit(1)

        return buffer

    def _parse_fragments(self, firmware=False):
        """ Parse fragments kbuild config and create config fragments """
        num = 0
        for fragment in self._fragments:
            content = ''
            if len(self._config_full) > 0:
                self._config_full += '+' + fragment
            else:
                self._config_full = fragment
            if fragment.startswith("cros://"):
                content = self._getcrosfragment(fragment)
            elif fragment.startswith("CONFIG_"):
                content = fragment + '\n'
            else:
                content = self.add_legacy_fragment(fragment)
            fragfile = os.path.join(self._fragments_dir, f"{num}.config")
            with open(fragfile, 'w') as f:
                f.write(content)
            # add fragment to artifacts but relative to artifacts dir
            frag_rel = os.path.relpath(fragfile, self._af_dir)
            self._artifacts.append(frag_rel)
            num += 1
        if firmware:
            content = 'CONFIG_EXTRA_FIRMWARE_DIR="'+self._firmware_dir+'"\n'
            fragfile = os.path.join(self._fragments_dir, f"{num}.config")
            with open(fragfile, 'w') as f:
                f.write(content)
            # add fragment to artifacts but relative to artifacts dir
            frag_rel = os.path.relpath(fragfile, self._af_dir)
            self._artifacts.append(frag_rel)
            num += 1
        return num

    def _merge_frags(self, fragnum):
        """ Merge config fragments to .config """
        # defconfig
        self.startjob("config_defconfig")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("make " + self._defconfig)
        # fragments
        self.startjob("config_fragments")
        for i in range(0, fragnum):
            self.addcmd("./scripts/kconfig/merge_config.sh" +
                        f" -m .config {self._fragments_dir}/{i}.config")
        # TODO: olddefconfig should be optional/configurable
        self.addcmd("make olddefconfig")
        self.addcmd("cd ..")

    def _generate_script(self):
        """ Generate shell script for complete build """
        # TODO(nuclearcat): Fetch firmware only if needed
        print("Generating shell script")
        self._fetch_firmware()
        fragnum = self._parse_fragments(firmware=True)
        self._merge_frags(fragnum)
        self._build_kernel()
        self._build_modules()
        self._package_kimage()
        self._package_modules()
        self._write_metadata()
        # dtb

        # terminate all active jobs
        self.startjob(None)
        # kill tail
        self.addcmd("kill $tailpid || true")
        print("Shell script generated")

    def write_script(self, filename):
        """ Write shell compile script to file """
        self._generate_script()
        with open(filename, 'w') as f:
            for step in self._steps:
                f.write(step + "\n")
        print(f"Script written to {filename}")

    def _build_kernel(self):
        """ Add kernel build steps """
        self.startjob("build_kernel")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_kimage.log and build_kimage_stderr.log
        self.addcmd("make -j$(nproc) " + MAKE_TARGETS[self._arch] +
                    " 1> " + self._af_dir + "/build_kimage.log" +
                    " 2> " + self._af_dir + "/build_kimage_stderr.log")
        self.addcmd("cd ..")

    def _build_modules(self):
        """ Add kernel modules build steps """
        self.startjob("build_modules")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_modules.log
        self.addcmd("make -j$(nproc) modules" + " 1> " +
                    self._af_dir + "/build_modules.log" +
                    " 2> " + self._af_dir + "/build_modules_stderr.log")

        self.addcmd("cd ..")

    def _package_kimage(self):
        """ Add kernel image packaging steps """
        self.startjob("package_kimage")
        self.addcmd("cd " + self._srcdir)
        # TODO(nuclearcat): Not all images might be present
        for img in KERNEL_IMAGE_NAMES[self._arch]:
            self.addcmd("cp arch/" + self._arch + "/boot/" + img + " ../artifacts", False)  # noqa
            # add image to artifacts relative to artifacts dir
            self._artifacts.append(img)
            break
        self.addcmd("cd ..")

    def _package_modules(self):
        """ Add kernel modules packaging steps """
        self.startjob("package_modules")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("make modules_install")
        self.addcmd(f"tar -C _modules_ -cJf {self._af_dir}/modules.tar.xz .")  # noqa
        self.addcmd("cd ..")
        self.addcmd("rm -rf _modules_")
        # add modules to artifacts relative to artifacts dir
        self._artifacts.append("modules.tar.xz")

    def _write_metadata(self):
        '''
        metadata.json for final step, that includes build info, artifacts, etc
        '''
        metadata = {}
        metadata['build'] = {}
        metadata['build']['arch'] = self._arch
        metadata['build']['compiler'] = self._compiler
        metadata['build']['defconfig'] = self._defconfig
        metadata['build']['fragments'] = self._fragments
        metadata['build']['srcdir'] = self._srcdir
        metadata['build']['config_full'] = self._config_full
        metadata['artifacts'] = self._artifacts
        with open(os.path.join(self._af_dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=4)

    def serialize(self, filename):
        """ Serialize class to json """
        # TODO(nuclearcat): Implement to_json method?
        data = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)  # noqa
        with open(filename, 'w') as f:
            f.write(data)
        print(f"Serialized to {filename}")

    def verify_build(self):
        '''
        Verify if artifacts exist, and if not - remove them from attributes
        '''
        new_artifacts = []
        for artifact in self._artifacts:
            abs_artifact = os.path.join(self._af_dir, artifact)
            if not os.path.exists(abs_artifact):
                print(f"{artifact} not found, removing")
            else:
                new_artifacts.append(artifact)
        self._artifacts = new_artifacts
        print("Artifacts verified")

    def _get_storage(self):
        '''
        Get storage object
        '''
        storage_config = kernelci.config.storage.StorageFactory.from_yaml(
            name='storage', config=yaml.safe_load(self._storage_config)
        )
        if not storage_config:
            return None
        storage_cred = os.getenv('KCI_STORAGE_CREDENTIALS')
        if not storage_cred:
            raise ValueError("KCI_STORAGE_CREDENTIALS not set")
        return kernelci.storage.get_storage(storage_config, storage_cred)

    def upload_artifacts(self):
        '''
        Upload artifacts to storage
        '''
        # TODO: Upload not using upload_single, but upload as multiple files
        print("[_upload_artifacts] Uploading artifacts to storage")
        node_af = {}
        storage = self._get_storage()
        root_path = '-'.join([self._apijobname, self._node['id']])
        for artifact in self._artifacts:
            artifact_path = os.path.join(self._af_dir, artifact)
            print(f"[_upload_artifacts] Uploading {artifact} to {root_path} artifact_path: {artifact_path}")  # noqa
            stored_url = storage.upload_single(
                (artifact_path, artifact), root_path
            )
            # Map ARTIFACT NAMES to ARTIFACT filename
            artifact = ARTIFACT_NAMES.get(artifact, artifact)

            node_af[artifact] = stored_url
            print(f"[_upload_artifacts] Uploaded {artifact} to {stored_url}")
        print("[_upload_artifacts] Artifacts uploaded to storage")
        return node_af

    def submit(self, retcode):
        '''
        Submit results to API and artifacts to storage
        '''
        af_uri = self.upload_artifacts()
        print("[_submit] Submitting results to API")
        api_token = os.environ.get('KCI_API_TOKEN')
        if not api_token:
            raise ValueError("KCI_API_TOKEN is not set")
        config = '/etc/kernelci/core/api-configs.yaml'
        configs = kernelci.config.load(config)
        api = 'staging.kernelci.org'
        api_config = configs['api'][api]
        api = kernelci.api.get_api(api_config, api_token)
        # TODO/FIXME: real detailed job result
        # pass fail skip incomplete
        if retcode != 0:
            job_result = 'fail'
        else:
            job_result = 'pass'
        artifacts = []
        for artifact in self._artifacts:
            artifacts.append(os.path.join(self._af_dir, artifact))

        # TODO(nuclearcat):
        # Add child_nodes for each sub-step
        results = {
            'node': {
                'name': self._apijobname,
                'result': job_result,
                'state': 'done',
                'artifacts': af_uri,
                'data': {
                    'kernel': {
                        'arch': self._arch,
                        'compiler': self._compiler,
                        'defconfig': self._defconfig,
                        'fragments': self._fragments,
                        'config_full': self._config_full,
                        'src_tarball': self._srctarball,
                    },
                },
            },
            'child_nodes': [],
        }

        node = self._node.copy()
        node.update(results['node'])
        api_helper = kernelci.api.helper.APIHelper(api)
        print(json.dumps(node, indent=2))
        print(json.dumps(results, indent=2))
        api_helper.submit_results(results, node)
        print(f"[_submit] Results submitted to API, node: {node['id']}")
        return results
