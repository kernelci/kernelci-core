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
- Implement 3-stage build process
  (fetch-prepare, build, package) with 3 containers
  (kernelci, compiler-specific, kernelci)

Available kbuild parameters:
- arch: architecture
- compiler: compiler
- defconfig: defconfig
- fragments: list of config fragments
- cross_compile: cross compile prefix
- cross_compile_compat: cross compile compat prefix
- dtbs_check: run "make dtbs_check" ONLY, it is actually a separate test
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
LEGACY_CONFIG = [
    'config/core/build-configs.yaml',
    '/etc/kernelci/core/build-configs.yaml',
]
FW_GIT = "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git"  # noqa

# TODO: find a way to automatically fetch this information
LATEST_LTS_MAJOR = 6
LATEST_LTS_MINOR = 6

DTBS_DISABLED = {
    'i386': True,
    'x86_64': True,
    'sparc': True,
    'um': True,
}

# Hard-coded make targets for each CPU architecture
MAKE_TARGETS = {
    'arm': 'zImage',
    'arm64': 'Image',
    'arc': 'uImage',
    'i386': 'bzImage',
    'x86_64': 'bzImage',
    'mips': 'uImage.gz',
    'riscv': 'Image',
    'riscv64': 'Image',
    'sparc': 'zImage',
    'um': 'linux'
}

# Hard-coded binary kernel image names for each CPU architecture
KERNEL_IMAGE_NAMES = {
    'arm': {'zImage', 'xipImage'},
    'arm64': {'Image'},
    'arc': {'uImage'},
    'i386': {'bzImage'},
    'mips': {'uImage.gz', 'vmlinux.gz.itb', 'vmlinuz'},
    'riscv': {'Image', 'Image.gz'},
    'riscv64': {'Image', 'Image.gz'},
    'sparc': {'zImage'},
    'x86_64': {'bzImage'},
    'x86': {'bzImage'},
    'um': {'linux'},
}

'''
Following convention is used for artifacts key
and filename mapping:
filename_regex - artifact name_regex
'''
ARTIFACT_NAMES = {
    r'modules\.tar\.gz': 'modules',
    r'modules\.tar\.xz': 'modules',
    r'build\.log': 'build_log',
    r'fragment/(\d)\.config': 'fragment\\1',
    r'metadata\.json': 'metadata',
}

# first argument stdout+stderr, second argument stderr only
REDIR = ' > >(tee {}) 2> >(tee {} >&1)'


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
    def __init__(self, node=None, jobname=None, params=None, jsonobj=None, apiconfig=None):
        # Retrieve and store API token for future use
        self._api_token = os.environ.get('KCI_API_TOKEN')
        if not self._api_token:
            raise ValueError("KCI_API_TOKEN is not set")

        # create new build object
        if node and jobname and params:
            self._workspace = None
            self._arch = params['arch']
            self._compiler = params['compiler']
            self._defconfig = params['defconfig']
            self._fragments = params['fragments']
            if 'cross_compile' in params:
                self._cross_compile = params['cross_compile']
            else:
                self._cross_compile = None
            if 'cross_compile_compat' in params:
                self._cross_compile_compat = params['cross_compile_compat']
            else:
                self._cross_compile_compat = None
            if 'dtbs_check' in params:
                self._dtbs_check = params['dtbs_check']
            else:
                self._dtbs_check = False
            self._disable_modules = params.get('disable_modules', False)
            self._apijobname = jobname
            self._steps = []
            self._artifacts = []
            self._current_job = None
            self._config_full = ''
            self._srcdir = None
            self._firmware_dir = None
            self._af_dir = None
            self._node = node
            self._api_yaml = apiconfig
            self._api_config = kernelci.config.api.API.load_from_yaml(
                yaml.safe_load(self._api_yaml), name='api'
            )
            self._full_artifacts = {}
            if node.get('debug') and 'tarball' in node['debug']:
                self._srctarball = node['debug']['tarball']
            elif node.get('artifacts') and 'tarball' in node['artifacts']:
                self._srctarball = node['artifacts']['tarball']
            else:
                api = kernelci.api.get_api(self._api_config, self._api_token)
                parent = api.node.get(self._node['parent'])
                if parent.get('artifacts') and 'tarball' in parent['artifacts']:
                    self._srctarball = parent['artifacts']['tarball']
                    return
                raise ValueError("No tarball artifact in input or parent node")
            return
        # load class from serialized json
        if jsonobj:
            self._arch = jsonobj['arch']
            self._compiler = jsonobj['compiler']
            self._defconfig = jsonobj['defconfig']
            self._fragments = jsonobj['fragments']
            self._cross_compile = jsonobj['cross_compile']
            self._cross_compile_compat = jsonobj['cross_compile_compat']
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
            self._api_yaml = jsonobj['api_yaml']
            self._api_config = kernelci.config.api.API.load_from_yaml(
                yaml.safe_load(self._api_yaml), name='api'
            )
            self._full_artifacts = jsonobj['full_artifacts']
            self._dtbs_check = jsonobj['dtbs_check']
            self._disable_modules = jsonobj['disable_modules']
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

    def set_api_config(self, api_yaml):
        """ Set API config """
        print(f"[_set_api_yaml] CONTENT: {api_yaml}")
        self._api_yaml = api_yaml

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
        if self._cross_compile:
            self.addcomment("  cross_compile: " + self._cross_compile)
        if self._cross_compile_compat:
            self.addcomment("  cross_compile_compat: " +
                            self._cross_compile_compat)
        self.addspacer()
        # set environment variables
        self.addcomment("Set environment variables")
        self.addcmd("export ARCH=" + self._arch)
        if self._cross_compile:
            self.addcmd("export CROSS_COMPILE=" + self._cross_compile)
        if self._cross_compile_compat:
            self.addcmd("export CROSS_COMPILE_COMPAT=" +
                        self._cross_compile_compat)
        self.addcmd("export INSTALL_MOD_PATH=_modules_")
        self.addcmd("export INSTALL_MOD_STRIP=1")
        self.addcmd("export INSTALL_DTBS_PATH=_dtbs_")
        # if self._compiler start with clang- we need to set env vars
        if self._compiler.startswith("clang-"):
            # LLVM=1, can be suffix with version in future, like -14
            self.addcmd("export LLVM=1")
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
        self._artifacts.append("build.sh")
        if not self._dtbs_check:
            self._artifacts.append("build_kimage.log")
            self._artifacts.append("build_kimage_stderr.log")
            if not self._disable_modules:
                self._artifacts.append("build_modules.log")
                self._artifacts.append("build_modules_stderr.log")
            self._artifacts.append("build_kselftest.log")
            self._artifacts.append("build_kselftest_stderr.log")
            # disable DTBS for some archs
            if self._arch not in DTBS_DISABLED:
                self._artifacts.append("build_dtbs.log")
                self._artifacts.append("build_dtbs_stderr.log")
        else:
            self._artifacts.append("build_dtbs_check.log")
            self._artifacts.append("build_dtbs_check_stderr.log")
        self._artifacts.append("metadata.json")
        # download tarball
        self.addcomment("Download tarball")
        self.addcmd("cd " + self._workspace)
        self.addcmd("wget -c -t 10 --retry-on-host-error \"" + self._srctarball + "\" -O linux.tgz")
        self.addcmd("tar -xzf linux.tgz -C " + self._srcdir + " --strip-components=1")

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
        cmd = f'echo job:{jobname}=running >> {self._af_dir}/state.txt'
        self._steps.append(cmd)
        cmd = f'echo jobsts:{jobname}=$(date +%s) >> {self._af_dir}/state.txt'
        self._steps.append(cmd)

    def addcmd(self, cmd, critical=True):
        '''
        critical - if True, check return code and exit, as command is critical
        '''
        if not critical:
            self._steps.append("echo Ignore error in next command, if any")
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
        # The ChromeOS kernel only has release branches for LTS kernels
        # so let's fall back to using the config for the latest LTS if
        # building a more recent version
        version = self._node['data']['kernel_revision']['version']
        target_rev = f"{version['version']}.{version['patchlevel']}"
        lts_rev = f"{LATEST_LTS_MAJOR}.{LATEST_LTS_MINOR}"
        if (target_rev in fragment and
            ((version['version'] > LATEST_LTS_MAJOR) or
             (version['version'] == LATEST_LTS_MAJOR and
              version['patchlevel'] > LATEST_LTS_MINOR))):
            print(f"Falling back to latest LTS config ({lts_rev}) " +
                  f"for kernel {target_rev}")
            fragment = fragment.replace(target_rev, lts_rev)
        buffer = ''
        [(branch, config)] = re.findall(r"cros://([\w\-.]+)/(.*)", fragment)
        cros_config = "/tmp/cros-config.tgz"
        url = CROS_CONFIG_URL.format(branch=branch)
        if not _download_file(url, cros_config):
            raise FileNotFoundError(f"Error reading {url}")
        with tarfile.open(cros_config) as tar:
            config_file_names = [
                'base.config',
                os.path.join(os.path.dirname(config), "common.config"),
                config,
            ]
            for file_name in config_file_names:
                try:
                    buffer += tar.extractfile(file_name).read().decode('utf-8')
                # In case the file isn't found a `KeyError` exception will be raised.
                # We should then retry extracting `chromeos/<file>` as it may be a
                # change in how the generated tarball is laid out.
                except KeyError:
                    buffer += tar.extractfile(os.path.join('chromeos', file_name)) \
                                 .read() \
                                 .decode('utf-8')

        os.unlink(cros_config)

        return (buffer, fragment)

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
        yml = None
        for cfg_path in LEGACY_CONFIG:
            if not os.path.exists(cfg_path):
                continue
            with open(cfg_path, 'r') as cfgfile:
                content = cfgfile.read()
                yml = yaml.safe_load(content)
                break

        if not yml:
            print(f"No suitable config file found in {LEGACY_CONFIG}")
            sys.exit(1)

        print(f"Searching for fragment {fragname} in {cfg_path}")
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
            if fragment.startswith("cros://"):
                (content, fragment) = self._getcrosfragment(fragment)
            elif fragment.startswith("CONFIG_"):
                content = fragment + '\n'
            else:
                content = self.add_legacy_fragment(fragment)
            fragfile = os.path.join(self._fragments_dir, f"{num}.config")
            with open(fragfile, 'w') as f:
                f.write(content)
            # add fragment to artifacts but relative to artifacts dir
            frag_rel = os.path.relpath(fragfile, self._af_dir)
            self._config_full += '+' + fragment
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
        if self._defconfig.startswith('cros://'):
            dotconfig = os.path.join(self._srcdir, ".config")
            with open(dotconfig, 'w') as f:
                (content, self._defconfig) = \
                    self._getcrosfragment(self._defconfig)
                f.write(content)
            self.addcmd("make olddefconfig")
        else:
            self.addcmd("make " + self._defconfig)
        self._config_full = self._defconfig + self._config_full
        # fragments
        self.startjob("config_fragments")
        for i in range(0, fragnum):
            self.addcmd("./scripts/kconfig/merge_config.sh" +
                        f" -m .config {self._fragments_dir}/{i}.config")
        # TODO: olddefconfig should be optional/configurable
        # TODO: log all warnings/errors of olddefconfig to separate file
        self.addcmd("make olddefconfig")
        self.addcmd(f"cp .config {self._af_dir}/")
        self.addcmd("cd ..")
        self._artifacts.append(".config")

    def _generate_script(self):
        """ Generate shell script for complete build """
        # TODO(nuclearcat): Fetch firmware only if needed
        print("Generating shell script")
        fragnum = self._parse_fragments(firmware=True)
        self._merge_frags(fragnum)
        if not self._dtbs_check:
            # TODO: verify if CONFIG_EXTRA_FIRMWARE have any files
            # We can check that if fragments have CONFIG_EXTRA_FIRMWARE
            self._fetch_firmware()
            self._build_kernel()
            if not self._disable_modules:
                self._build_modules()
            self._build_kselftest()
            if self._arch not in DTBS_DISABLED:
                self._build_dtbs()
            self._package_kimage()
            if not self._disable_modules:
                self._package_modules()
            self._package_kselftest()
            if self._arch not in DTBS_DISABLED:
                self._package_dtbs()
        else:
            self._build_dtbs_check()
        self._write_metadata()
        # terminate all active jobs
        self.startjob(None)
        # indicate script is ended
        self.addcmd("echo Build script is completed, tail will be killed now")
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
        # copy to artifacts dir
        os.system(f"cp {filename} {self._af_dir}/build.sh")

    def _build_kernel(self):
        """ Add kernel build steps """
        self.startjob("build_kernel")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_kimage.log and build_kimage_stderr.log
        self.addcmd("make -j$(nproc) " + MAKE_TARGETS[self._arch] + " " +
                    REDIR.format(self._af_dir + "/build_kimage.log",
                                 self._af_dir + "/build_kimage_stderr.log"))
        self.addcmd("cd ..")

    def _build_modules(self):
        """ Add kernel modules build steps """
        self.startjob("build_modules")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_modules.log
        self.addcmd("make -j$(nproc) modules " +
                    REDIR.format(self._af_dir + "/build_modules.log",
                                 self._af_dir + "/build_modules_stderr.log"))
        self.addcmd("cd ..")

    def _build_dtbs(self):
        """ Add kernel dtbs build steps """
        self.startjob("build_dtbs")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_dtbs.log
        self.addcmd("make -j$(nproc) dtbs " +
                    REDIR.format(self._af_dir + "/build_dtbs.log",
                                 self._af_dir + "/build_dtbs_stderr.log"), False)
        self.addcmd("cd ..")

    def _build_kselftest(self):
        """ Add kselftest build steps """
        self.startjob("build_kselftest")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_kselftest.log
        self.addcmd("make -j$(nproc) kselftest-gen_tar " +
                    REDIR.format(self._af_dir + "/build_kselftest.log",
                                 self._af_dir + "/build_kselftest_stderr.log"), False)

    def _build_dtbs_check(self):
        """ Check if dtbs are present """
        self.startjob("build_dtbs_check")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("make -j$(nproc) dtbs_check" + " --output-sync " +
                    REDIR.format(self._af_dir + "/build_dtbs_check.log",
                                 self._af_dir + "/build_dtbs_check_stderr.log") +
                    " && echo DTBS_CHECK_OK || echo DTBS_CHECK_FAILED $?", False)
        self.addcmd("cd ..")

    def _package_kimage(self):
        """ Add kernel image packaging steps """
        self.startjob("package_kimage")
        self.addcmd("cd " + self._srcdir)
        # TODO(nuclearcat): Not all images might be present
        for img in KERNEL_IMAGE_NAMES[self._arch]:
            self.addcmd("cp arch/" + self._arch + "/boot/" + img + " ../artifacts", False)
            # add image to artifacts relative to artifacts dir
            self._artifacts.append(img)
        self.addcmd("cd ..")

    def _package_modules(self):
        """ Add kernel modules packaging steps """
        self.startjob("package_modules")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("make modules_install")
        self.addcmd(f"tar -C _modules_ -cJf {self._af_dir}/modules.tar.xz .")
        self.addcmd("cd ..")
        self.addcmd("rm -rf _modules_")
        # add modules to artifacts relative to artifacts dir
        self._artifacts.append("modules.tar.xz")

    def _package_kselftest(self):
        """ Add kselftest packagin steps """
        self.startjob("package_kselftest")
        self.addcmd(f"cp {self._srcdir}/tools/testing/selftests/kselftest_install/" +
                    "kselftest-packages/kselftest.tar.gz " +
                    f"{self._af_dir}/", False)
        self._artifacts.append("kselftest.tar.gz")

    def _package_dtbs(self):
        """ Add kernel dtbs packaging steps """
        self.startjob("package_dtbs")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("make dtbs_install", False)
        # create dtbs dir in artifacts
        self.addcmd(f"mkdir -p {self._af_dir}/dtbs")
        # copy dtbs to artifacts
        self.addcmd(f"cp -r _dtbs_/* {self._af_dir}/dtbs", False)
        self.addcmd("cd ..")

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

        with open(os.path.join(self._af_dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=4)

    def serialize(self, filename):
        """ Serialize class to json """
        # TODO(nuclearcat): Implement to_json method?
        data = json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
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
        # If we have dtbs dir, add it to artifacts
        dtbs_dir = os.path.join(self._af_dir, "dtbs")
        if os.path.exists(dtbs_dir):
            # walk and add each dtb file
            for root, dirs, files in os.walk(dtbs_dir):
                for file in files:
                    if file.endswith(".dtb"):
                        # we need to truncate abs path to relative to artifacts
                        file = os.path.relpath(os.path.join(root, file),
                                               self._af_dir)
                        self._artifacts.append(file)
        # Update manifest/metadata
        self._write_metadata()
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

    def map_artifact_name(self, artifact):
        '''
        Map artifact name to filename
        '''
        for key in ARTIFACT_NAMES:
            if re.match(key, artifact):
                return re.sub(key, ARTIFACT_NAMES[key], artifact)
        # otherwise map all dots to underscores
        artifact = artifact.replace('.', '_')
        return artifact

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
            compressed_file = False
            artifact_path = os.path.join(self._af_dir, artifact)
            print(f"[_upload_artifacts] Uploading {artifact} to {root_path} "
                  f"artifact_path: {artifact_path}")
            # small discourse, if it is .log file - compress it, but keep original
            # upload .gz. then delete this gz
            if artifact.endswith(".log"):
                os.system(f"gzip -k {artifact_path}")
                artifact_path = artifact_path + ".gz"
                compressed_file = True
                dst_filename = artifact + ".gz"
            else:
                dst_filename = artifact
            stored_url = storage.upload_single(
                (artifact_path, dst_filename), root_path
            )
            self._full_artifacts[artifact] = stored_url
            artifact_key = self.map_artifact_name(artifact)
            # map bzImage, zImage, Image,etc to "kernel"
            if artifact in KERNEL_IMAGE_NAMES[self._arch]:
                node_af['kernel'] = stored_url
                # Future jobs can expect the kernel "type" as a parameter,
                # which is actually the lowercase version of the kernel image
                # filename
                self._node['data']['kernel_type'] = artifact.lower()
            else:
                node_af[artifact_key] = stored_url
            if compressed_file:
                os.unlink(artifact_path)
            print(f"[_upload_artifacts] Uploaded {artifact} to {stored_url}")
        print("[_upload_artifacts] Artifacts uploaded to storage")
        return node_af

    def upload_metadata(self):
        '''
        Upload metadata.json to storage
        '''
        print("[_upload_metadata] Uploading metadata.json to storage")
        storage = self._get_storage()
        root_path = '-'.join([self._apijobname, self._node['id']])
        metadata_path = os.path.join(self._af_dir, "metadata.json")
        stored_url = storage.upload_single(
            (metadata_path, "metadata.json"), root_path
        )
        print(f"[_upload_metadata] Uploaded metadata.json to {stored_url}")
        print("[_upload_metadata] metadata.json uploaded to storage")
        return stored_url

    def _update_metadata(self, job_result):
        '''
        Update metadata.json with artifacts and job result
        '''
        metadata_file = os.path.join(self._af_dir, "metadata.json")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        metadata['artifacts'] = self._full_artifacts
        metadata['build']['result'] = job_result
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)

    def submit(self, retcode, dry_run=False):
        '''
        Submit results to API and artifacts to storage
        '''
        af_uri = None
        # When in dry run, get the node's artifacts first otherwise
        # they could be overwritten by refreshing the node further down
        if dry_run:
            if self._node.get('artifacts'):
                af_uri = self._node['artifacts']
            else:
                af_uri = {'tarball': 'http://dry-run.test/tarball'}
        api = kernelci.api.get_api(self._api_config, self._api_token)
        # Update node from API, as we might have new fields
        # such as k8s_context
        node_id = self._node['id']
        self._node = api.node.get(node_id)
        # Ensure upload_artifacts() is called *after* refreshing the node
        # as we add a new field to its data in this function
        if af_uri is None:
            af_uri = self.upload_artifacts()
        print("[_submit] Submitting results to API")
        # TODO/FIXME: real detailed job result
        # pass fail skip incomplete
        if retcode != 0:
            job_result = 'fail'
        else:
            job_result = 'pass'
        artifacts = []
        for artifact in self._artifacts:
            artifacts.append(os.path.join(self._af_dir, artifact))
        # Add full artifacts path to metadata.json
        # We do it after full artifacts upload, twice
        # as we can get urls of artifacts AFTER upload
        self._update_metadata(job_result)
        # Upload metadata.json to storage
        metadata_uri = self.upload_metadata()
        af_uri['metadata'] = metadata_uri

        # do we have dtbs/ in af_uri?
        dtb_present = False
        for artifact in af_uri:
            if artifact.startswith('dtbs/'):
                dtb_present = True
                break

        if dtb_present:
            af_uri = {k: v for k, v in af_uri.items()
                      if not k.startswith('dtbs/')}

        # if this is dtbs_check and it ran ok, we need to change job_result
        # to actual result of dtbs_check
        if self._dtbs_check and job_result == 'pass':
            # open build.log and search for DTBS_CHECK_FAILED or DTBS_CHECK_OK
            with open(os.path.join(self._af_dir, "build.log"), 'r') as f:
                log = f.read()
                if "DTBS_CHECK_FAILED" in log:
                    print("[_submit] DTBS_CHECK_FAILED in build.log")
                    job_result = 'fail'
                elif "DTBS_CHECK_OK" in log:
                    print("[_submit] DTBS_CHECK_OK in build.log")
                    job_result = 'pass'
                # this is just for testing child nodes
                else:
                    print("[_submit] No DTBS_CHECK in build.log")
                    job_result = 'skip'

        # TODO(nuclearcat):
        # Add child_nodes for each sub-step
        results = {
            'node': {
                'name': self._apijobname,
                'result': job_result,
                'state': 'done',
                'artifacts': af_uri,
            },
            'child_nodes': []
        }

        node = self._node.copy()
        results['node']['data'] = node['data']
        results['node']['data']['arch'] = self._arch
        results['node']['data']['compiler'] = self._compiler
        results['node']['data']['defconfig'] = self._defconfig
        results['node']['data']['fragments'] = self._fragments
        results['node']['data']['config_full'] = self._config_full
        api_helper = kernelci.api.helper.APIHelper(api)
        api_helper.submit_results(results, node)
        print(f"[_submit] submit_results to API, node: {node['id']}")
        return results
