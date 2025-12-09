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
- kselftest: false - do not build kselftest
"""

from datetime import datetime, timedelta
import os
import sys
import re
import tarfile
import json
import requests
import time
import yaml
import concurrent.futures
import threading
import subprocess
import kernelci.api
import kernelci.api.helper
import kernelci.config
import kernelci.config.storage
import kernelci.storage
from typing import Dict, Tuple, List

CIP_CONFIG_URL = \
    "https://gitlab.com/cip-project/cip-kernel/cip-kernel-config/-/raw/master/{branch}/{config}"  # noqa
CROS_CONFIG_URL = \
    "https://chromium.googlesource.com/chromiumos/third_party/kernel/+archive/refs/heads/{branch}/chromeos/config.tar.gz"  # noqa
FW_GIT = "https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git"  # noqa

# TODO: find a way to automatically fetch this information
LATEST_LTS_MAJOR = 6
LATEST_LTS_MINOR = 12

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
    'arm64': {'Image', 'Image.gz'},
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


def _download_file_inner(url, file_path):
    try:
        r = requests.get(url, stream=True, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"[_download_file_inner] Error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"[_download_file_inner] Timeout: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[_download_file_inner] Connection error: {e}")
        return False
    except Exception as e:
        print(f"[_download_file_inner] Exception: {e}")
        return False
    if r.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
        return True


def _download_file(url, file_path):
    '''
    Download file to file_path
    TODO(nuclearcat): Do we have anything generic in KernelCI for this?
    '''
    print(f"[_download_file] Downloading {url} to {file_path}")
    retries = 10
    while retries > 0:
        if _download_file_inner(url, file_path):
            return True
        time.sleep(5)
        retries -= 1
    return False


class KBuild():
    '''
    Build class that represents kernel build
    if node, jobname and params are provided, create new build object
    if jsonobj is provided, load class from serialized json
    '''
    def __init__(self, node=None, jobname=None, params=None, jsonobj=None, apiconfig=None,
                 fragment_configs=None):
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
            # if defconfig contains '+', it means it is a list
            if isinstance(self._defconfig, str) and '+' in self._defconfig:
                self._defconfig = self._defconfig.split('+')
            self._backend = params.get('backend', 'make')
            # Support USE_TUXMAKE environment variable for backward compatibility
            if os.environ.get('USE_TUXMAKE') == '1':
                self._backend = 'tuxmake'
            self._fragments = params['fragments']
            self._fragment_configs = fragment_configs or {}
            if 'coverage' in self._fragments:
                self._coverage = True
            else:
                self._coverage = False
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
            if params.get('kselftest') == 'disable':
                self._kfselftest = False
            else:
                self._kfselftest = True
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
            self._fragment_configs = jsonobj.get('fragment_configs', {})
            self._backend = jsonobj.get('backend', 'make')
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
            self._kfselftest = jsonobj['kfselftest']
            self._coverage = jsonobj.get('coverage', False)
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
        # Add comments about build metadata
        self.addcomment("Build metadata:")
        self.addcomment("  arch: " + self._arch)
        self.addcomment("  compiler: " + self._compiler)
        if isinstance(self._defconfig, str):
            self.addcomment("  defconfig: " + self._defconfig)
        if isinstance(self._defconfig, list):
            self.addcomment("  defconfig: " + ' '.join(self._defconfig))
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
        if self._backend != 'tuxmake':
            if self._cross_compile:
                self.addcmd("export CROSS_COMPILE=" + self._cross_compile)
            if self._cross_compile_compat:
                self.addcmd("export CROSS_COMPILE_COMPAT=" +
                            self._cross_compile_compat)
            self.addcmd("export INSTALL_MOD_PATH=_modules_")
            self.addcmd("export INSTALL_MOD_STRIP=1")
            self.addcmd("export INSTALL_DTBS_PATH=_dtbs_")
            self.addcmd("export CC=" + self._compiler)
            self.addcmd("export HOSTCC=" + self._compiler)
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
        if self._backend != 'tuxmake':
            if not self._dtbs_check:
                self._artifacts.append("build_kimage.log")
                self._artifacts.append("build_kimage_stderr.log")
                self._artifacts.append("build_modules.log")
                self._artifacts.append("build_modules_stderr.log")
                if self._kfselftest:
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

    def addcmdretry(self, cmd, retries=10):
        '''
        Retry command if it fails up to retries times
        '''
        self.addcomment(f"Retry command {cmd} {retries} times")
        self.addcmd("for i in $(seq 1 " + str(retries) + "); do")
        self.addcmd("  echo \"Attempt $i\"")
        self.addcmd("  sleep 1")
        self.addcmd("  " + cmd + " && break")
        self.addcmd("done")
        self.addcmd("if [ $? -ne 0 ]; then")
        self.addcmd("  echo \"Failed to run " + cmd + "\"")
        self.addcmd("  exit 1")
        self.addcmd("fi")

    def addcmd(self, cmd, critical=True):
        '''
        critical - if True, check return code and exit, as command is critical
        '''
        if not critical:
            self._steps.append("echo Ignore error in next command, if any")
            cmd += " || true"
        self._steps.append(cmd)

    def enable_trap(self):
        """ Enable trap for error handling, if shell script fails """
        en_trap = """
set -eE -o pipefail

trap 'case $stage in
          0) exit 0;;        # success
          1) exit 1;;        # any build command failed
          2) exit 2;;        # any test command failed
          *) exit $?;        # fallback for unexpected errors
      esac' ERR
"""
        self._steps.append(en_trap)

    def disable_trap(self):
        """ Disable trap for error handling,
        if we have for example command EXPECTED to fail """
        dis_trap = """set +eE -o pipefail
trap - ERR
"""
        self._steps.append(dis_trap)

    def _fetch_firmware(self):
        '''
        Fetch firmware from linux-firmware repo
        TODO: Implement caching and optional fetch
        TODO: Implement firmware commit id meta/settings
        '''
        self.startjob("fetch_firmware")
        # self.addcmdretry(f"git clone {FW_GIT} --depth 1", 10)
        # This file available https://storage.kernelci.org/linux-firmware.tar.gz
        # we download it there for better reliability
        # self.addcmd("wget -c -t 10 --retry-on-host-error " +
        #            "https://storage.kernelci.org/linux-firmware.tar.gz -O linux-firmware.tar.gz")
        # We should have cached copy of linux-firmware.tar.gz at /data directory
        self.addcmd("cp /data/linux-firmware.tar.gz .")
        self.addcmd("tar -xzf linux-firmware.tar.gz")
        self.addcmd("cd linux-firmware")
        self.addcmd("./copy-firmware.sh " + self._firmware_dir)
        self.addcmd("cd ..")
        # self.addcmd("rm -rf linux-firmware")

    def _download_file(self, url):
        """ Download file from url and return it in buffer """
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
        return None

    def _getcipfragment(self, fragment):
        """ Get CIP specific configuration fragments """
        [(branch, config)] = re.findall(r"cip://([\w\-.]+)/(.*)", fragment)
        url = CIP_CONFIG_URL.format(branch=branch, config=config)
        buffer = self._download_file(url)
        if not buffer:
            raise FileNotFoundError("Error reading {}".format(url))
        try:
            plain_str = buffer.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("Error decoding {}".format(url))
        return plain_str

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

    def _verify_network(self):
        """ Verify network connectivity """
        # TBD: Different URL? pool of urls?
        retries = 10
        while retries > 0:
            try:
                r = requests.get("https://google.com")
            except Exception as e:
                print(f"[_verify_network] Error: {e}")
                time.sleep(5)
                retries -= 1
                continue
            if r.status_code == 200:
                return
            time.sleep(5)

        print("[_verify_network] Network is not available")
        sys.exit(1)

    def extract_config(self, frag):
        """ Extract config fragments from legacy config file """
        txt = ''
        config = frag.get('configs', None)
        if not config:
            print("No configs section in fragment")
            config = []

        for c in config:
            txt += c + '\n'
        return txt

    def add_fragment(self, fragname):
        """ Get config fragment from passed fragment_configs """
        if fragname not in self._fragment_configs:
            print(f"Fragment {fragname} not found in fragment_configs")
            self.submit_failure(f"Fragment {fragname} not found in fragment_configs")
            sys.exit(1)

        frag = self._fragment_configs[fragname]
        print(f"Using fragment {fragname} from inline configs")
        return self.extract_config(frag)

    def _parse_fragments(self, firmware=False):
        """ Parse fragments kbuild config and create config fragments

        Returns:
            list: List of fragment file paths
        """
        fragment_files = []

        for idx, fragment in enumerate(self._fragments):
            content = ''
            fragment_name = fragment

            if fragment.startswith("cros://"):
                (content, fragment_name) = self._getcrosfragment(fragment)
            elif fragment.startswith("cip://"):
                content = self._getcipfragment(fragment)
            elif fragment.startswith("CONFIG_"):
                content = fragment + '\n'
            else:
                # Use fragment configs passed from scheduler
                content = self.add_fragment(fragment)

            if not content:
                print(f"[_parse_fragments] WARNING: Fragment {fragment} has no content")
                continue

            fragfile = os.path.join(self._fragments_dir, f"{idx}.config")
            with open(fragfile, 'w') as f:
                f.write(content)

            config_count = len([line for line in content.split('\n') if line.strip()])
            print(f"[_parse_fragments] Created {fragfile} ({config_count} configs)")

            fragment_files.append(fragfile)

            # add fragment to artifacts but relative to artifacts dir
            frag_rel = os.path.relpath(fragfile, self._af_dir)
            self._config_full += '+' + fragment_name
            self._artifacts.append(frag_rel)

        if firmware:
            content = 'CONFIG_EXTRA_FIRMWARE_DIR="'+self._firmware_dir+'"\n'
            fragfile = os.path.join(self._fragments_dir, f"{len(self._fragments)}.config")
            with open(fragfile, 'w') as f:
                f.write(content)

            fragment_files.append(fragfile)

            # add fragment to artifacts but relative to artifacts dir
            frag_rel = os.path.relpath(fragfile, self._af_dir)
            self._artifacts.append(frag_rel)

        print(f"[_parse_fragments] Created {len(fragment_files)} fragment files")
        return fragment_files

    def _merge_frags(self, fragment_files):
        """ Merge config fragments to .config

        Args:
            fragment_files: List of fragment file paths to merge
        """
        self.startjob("config_defconfig")
        self.addcmd("cd " + self._srcdir)
        if isinstance(self._defconfig, str) and self._defconfig.startswith('cros://'):
            dotconfig = os.path.join(self._srcdir, ".config")
            with open(dotconfig, 'w') as f:
                (content, self._defconfig) = \
                    self._getcrosfragment(self._defconfig)
                f.write(content)
            self.addcmd("make olddefconfig")
            self._config_full = self._defconfig + self._config_full
        else:
            if isinstance(self._defconfig, str):
                self.addcmd("make " + self._defconfig)
                self._config_full = self._defconfig + self._config_full
            # we allow multiple defconfigs or make targets
            # such as: make defconfig allnoconfig hardened.config
            if isinstance(self._defconfig, list):
                defconfigs = ' '.join(self._defconfig)
                self.addcmd("make " + defconfigs)
                defconfigs = '+'.join(self._defconfig)
                self._config_full = defconfigs + self._config_full
        # fragments
        self.startjob("config_fragments")
        for fragfile in fragment_files:
            self.addcmd(f"./scripts/kconfig/merge_config.sh -m .config {fragfile}")
        # TODO: olddefconfig should be optional/configurable
        # TODO: log all warnings/errors of olddefconfig to separate file
        self.addcmd("make olddefconfig")
        self.addcmd(f"cp .config {self._af_dir}/")
        self.addcmd("cd ..")
        self._artifacts.append(".config")

    def _generate_script(self):
        """ Generate shell script for complete build """
        print("Generating shell script")
        self._fragment_files = self._parse_fragments(firmware=True)

        if self._backend == 'tuxmake':
            self._build_with_tuxmake()
        else:
            self._merge_frags(self._fragment_files)
            self._build_with_make()

        self._write_metadata()
        # terminate all active jobs
        self.startjob(None)
        # indicate script is ended
        self.addcmd("echo Build script is completed, tail will be killed now")
        self.addcmd("stage=0")
        self.disable_trap()
        # kill tail
        self.addcmd("kill $tailpid || true")
        print("Shell script generated")

    def write_script(self, filename):
        """ Write shell compile script to file """
        self._verify_network()
        self._generate_script()
        fixed_header = """#!/bin/bash
set -eE -o pipefail          # -E ⇒ trap inherits in functions/subshells

stage=2                      # 1 = build, 2 = infrastructure

trap 'case $stage in
          0) exit 0;;        # any build command succeeded
          1) exit 1;;        # any build command failed
          2) exit 2;;        # any test command failed
          *) exit $?;        # fallback for unexpected errors
      esac' ERR

"""
        with open(filename, 'w') as f:
            f.write(fixed_header)
            for step in self._steps:
                f.write(step + "\n")
            f.write("stage=0\n")
            f.write("kill $tailpid || true\n")
        print(f"Script written to {filename}")
        # copy to artifacts dir
        os.system(f"cp {filename} {self._af_dir}/build.sh")

    def _build_with_make(self):
        """ Build kernel using make """
        if not self._dtbs_check:
            self._fetch_firmware()
            self._build_kernel()
            self._build_modules()
            if self._kfselftest:
                self._build_kselftest()
            if self._arch not in DTBS_DISABLED:
                self._build_dtbs()
            self._package_kimage()
            self._package_modules()
            if self._coverage:
                self._package_coverage()
            if self._kfselftest:
                self._package_kselftest()
            if self._arch not in DTBS_DISABLED:
                self._package_dtbs()
        else:
            self._build_dtbs_check()

    def _build_with_tuxmake(self):
        """ Build kernel using tuxmake with native fragment support """
        print("[_build_with_tuxmake] Starting tuxmake build")

        if not hasattr(self, '_fragment_files'):
            print("[_build_with_tuxmake] ERROR: No fragment files available")
            self._fragment_files = []

        print(f"[_build_with_tuxmake] Using {len(self._fragment_files)} fragment files")

        # Handle defconfigs - first goes to --kconfig, rest to --kconfig-add
        extra_defconfigs = []
        if isinstance(self._defconfig, list):
            defconfig = self._defconfig[0]
            extra_defconfigs = self._defconfig[1:]
            self._config_full = '+'.join(self._defconfig) + self._config_full
        elif isinstance(self._defconfig, str):
            defconfig = self._defconfig
            self._config_full = self._defconfig + self._config_full
        else:
            defconfig = 'defconfig'
            print("[_build_with_tuxmake] WARNING: No defconfig specified, using 'defconfig'")

        # Fetch firmware for builds that need it
        self._fetch_firmware()

        self.startjob("build_tuxmake")
        self.addcmd("cd " + self._srcdir)

        # Handle ChromeOS defconfig: write fragments to a file and pass
        # as --kconfig-add on top of defconfig
        if defconfig.startswith('cros://'):
            print(f"[_build_with_tuxmake] Handling ChromeOS defconfig: {defconfig}")
            content, _ = self._getcrosfragment(defconfig)
            cros_config = os.path.join(self._af_dir, "chromeos.config")
            with open(cros_config, 'w') as f:
                f.write(content)
            defconfig = 'defconfig'
            extra_defconfigs.insert(0, cros_config)

        cmd_parts = [
            "tuxmake --runtime=null",
            f"--target-arch={self._arch}",
            f"--toolchain={self._compiler}",
            f"--output-dir={self._af_dir}",
        ]

        cmd_parts.append(f"--kconfig={defconfig}")
        for extra in extra_defconfigs:
            cmd_parts.append(f"--kconfig-add={extra}")
            print(f"[_build_with_tuxmake] Adding extra defconfig: {extra}")

        for fragfile in self._fragment_files:
            if os.path.exists(fragfile):
                cmd_parts.append(f"--kconfig-add={fragfile}")
                print(f"[_build_with_tuxmake] Adding fragment: {os.path.basename(fragfile)}")
            else:
                print(f"[_build_with_tuxmake] WARNING: Fragment file not found: {fragfile}")

        # Build targets: kernel modules, plus dtbs if arch supports it
        targets = ["kernel", "modules"]
        if self._arch not in DTBS_DISABLED:
            targets.append("dtbs")
            if self._kfselftest:
                targets.append("kselftest")
        cmd_parts.append(" ".join(targets))
        print(f"[_build_with_tuxmake] Building targets: {' '.join(targets)}")

        tuxmake_cmd = " ".join(cmd_parts)
        print(f"[_build_with_tuxmake] Command: {tuxmake_cmd}")
        print(f"[_build_with_tuxmake] Output directory: {self._af_dir}")
        self.addcmd(tuxmake_cmd)

        # tuxmake outputs 'config' (no dot), rename to '.config' for consistency
        self.addcmd(
            f"[ -f {self._af_dir}/config ] && "
            f"mv {self._af_dir}/config {self._af_dir}/.config"
        )

        self.addcmd("cd ..")

    def _build_kernel(self):
        """ Add kernel build steps """
        self.startjob("build_kernel")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_kimage.log and build_kimage_stderr.log
        self.addcmd("stage=1")  # stage 1 failure is kernel build failure
        self.addcmd("make -j$(nproc) " + MAKE_TARGETS[self._arch] + " " +
                    REDIR.format(self._af_dir + "/build_kimage.log",
                                 self._af_dir + "/build_kimage_stderr.log"))
        self.addcmd("stage=2")
        self.addcmd("cd ..")

    def _build_modules(self):
        """ Add kernel modules build steps """
        self.startjob("build_modules")
        self.addcmd("cd " + self._srcdir)
        self.disable_trap()
        # Add conditional block for modules build
        self.addcmd("grep \"CONFIG_MODULES=y\" .config")
        # << CONDITIONAL START >>
        self.addcmd("if [ $? -eq 0 ]; then")
        self.enable_trap()
        # output to separate build_modules.log
        self.addcmd("stage=1")
        self.addcmd("make -j$(nproc) modules " +
                    REDIR.format(self._af_dir + "/build_modules.log",
                                 self._af_dir + "/build_modules_stderr.log"))
        # << CONDITIONAL END >>
        self.addcmd("stage=2")
        self.addcmd("fi")
        self.enable_trap()
        # was -e here
        self.addcmd("cd ..")

    def _build_dtbs(self):
        """ Add kernel dtbs build steps """
        self.startjob("build_dtbs")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_dtbs.log
        self.addcmd("stage=1")  # stage 1 failure is kernel build failure
        self.addcmd("make -j$(nproc) dtbs " +
                    REDIR.format(self._af_dir + "/build_dtbs.log",
                                 self._af_dir + "/build_dtbs_stderr.log"), False)
        self.addcmd("stage=2")
        self.addcmd("cd ..")

    def _build_kselftest(self):
        """ Add kselftest build steps """
        self.startjob("build_kselftest")
        self.addcmd("cd " + self._srcdir)
        # output to separate build_kselftest.log
        self.addcmd("stage=1")  # stage 1 failure is kselftest build failure
        self.addcmd("make -j$(nproc) kselftest-gen_tar " +
                    REDIR.format(self._af_dir + "/build_kselftest.log",
                                 self._af_dir + "/build_kselftest_stderr.log"), False)
        self.addcmd("stage=2")

    def _build_dtbs_check(self):
        """ Check if dtbs are present """
        self.startjob("build_dtbs_check")
        self.addcmd("cd " + self._srcdir)
        self.addcmd("stage=1")
        self.addcmd("make -j$(nproc) dtbs_check" + " --output-sync " +
                    REDIR.format(self._af_dir + "/build_dtbs_check.log",
                                 self._af_dir + "/build_dtbs_check_stderr.log") +
                    " && echo DTBS_CHECK_OK || echo DTBS_CHECK_FAILED $?", False)
        self.addcmd("stage=2")
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
        # https://github.com/kernelci/kernelci-project/issues/509
        self.addcmd("cp vmlinux ../artifacts", False)
        self._artifacts.append("vmlinux")
        self.addcmd("cd ..")

    def _package_modules(self):
        """ Add kernel modules packaging steps """
        self.startjob("package_modules")
        self.addcmd("cd " + self._srcdir)
        # Add conditional block for modules install
        # disable quit on error, as we don't want to fail if no modules
        self.disable_trap()
        self.addcmd("grep \"CONFIG_MODULES=y\" .config")
        # << CONDITIONAL START >>
        self.addcmd("if [ $? -eq 0 ]; then")
        self.enable_trap()
        self.addcmd("stage=1")  # stage 1 failure is kernel build failure
        self.addcmd("make modules_install")
        self.addcmd("stage=2")  # stage 2 failure is infrastructure failure
        self.addcmd(f"tar -C _modules_ -cJf {self._af_dir}/modules.tar.xz .")
        self.addcmd("cd ..")
        self.addcmd("rm -rf _modules_")
        # << ELSE >>
        self.addcmd("else")
        self.enable_trap()
        self.addcmd("echo \"No modules to install\"")
        self.addcmd("cd ..")
        # << CONDITIONAL END >>
        self.addcmd("fi")
        # add modules to artifacts relative to artifacts dir
        self._artifacts.append("modules.tar.xz")
        self.enable_trap()

    def _package_coverage(self):
        """ Add coverage source packaging steps """
        self.startjob("package_coverage")
        self.addcmd("cd " + self._srcdir)
        # Add conditional block for gcov packing
        # Disable quit on error, as we don't want to fail here
        self.disable_trap()
        # << CONDITIONAL START >>
        self.addcmd("if grep -q \"CONFIG_GCOV_KERNEL=y\" .config; then")
        # gcov needs both the source code **as configured for the build** (including
        # symlinks) and coverage data (*.gcno files)
        # See https://www.kernel.org/doc/html/v6.12/dev-tools/gcov.html for details
        self.addcmd(f"find {self._srcdir} \\( -name '*.gcno' -o -name '*.[ch]' " +
                    "-o -type l \\) -a -perm /u+r,g+r | tar cJf " +
                    f"{self._af_dir}/coverage_source.tar.xz -P -T -", False)
        # << CONDITIONAL END >>
        self.addcmd("fi")
        self.enable_trap()
        self._artifacts.append("coverage_source.tar.xz")

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
        metadata['build']['backend'] = self._backend

        with open(os.path.join(self._af_dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=4)

    def serialize(self, filename):
        """ Serialize class to json

        Note: Uses __dict__ to serialize all instance attributes (including
        _backend, _arch, etc). The from_json() method strips underscore
        prefixes when loading, so _backend becomes 'backend' in jsonobj.
        """
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
        Upload artifacts to storage using parallel processing
        '''
        print("[_upload_artifacts] Uploading artifacts to storage")

        # Thread-safe dictionaries for results
        node_af = {}
        node_af_lock = threading.Lock()

        storage = self._get_storage()
        root_path = '-'.join([self._apijobname, self._node['id']])

        # Prepare all artifacts for upload
        upload_tasks = []
        if self._backend == 'tuxmake':
            # For TuxMake, upload everything in artifacts directory
            print("[_upload_artifacts] TuxMake backend: discovering files in artifacts dir")
            for root, dirs, files in os.walk(self._af_dir):
                for file in files:
                    file_rel = os.path.relpath(os.path.join(root, file), self._af_dir)
                    artifact_path = os.path.join(self._af_dir, file_rel)
                    upload_tasks.append((file_rel, artifact_path))
        else:
            # For make backend, upload only listed artifacts
            for artifact in self._artifacts:
                artifact_path = os.path.join(self._af_dir, artifact)
                upload_tasks.append((artifact, artifact_path))

        # Function to handle a single artifact upload
        # args: (artifact, artifact_path)
        # returns: (artifact, stored_url, error)
        def process_and_upload_artifact(task: Tuple[str, str]) -> Tuple[str, str, str]:
            artifact, artifact_path = task
            compressed_file = False
            dst_filename = artifact
            upload_path = artifact_path

            print(f"[_upload_artifacts] Processing {artifact}")

            # Handle compression
            if artifact.endswith(".log"):
                # Use subprocess for better control and error handling
                subprocess.run(['gzip', '-k', artifact_path], check=True)
                upload_path = artifact_path + ".gz"
                compressed_file = True
                dst_filename = artifact + ".gz"
            elif artifact == "vmlinux":
                subprocess.run(['xz', '-k', artifact_path], check=True)
                upload_path = artifact_path + ".xz"
                compressed_file = True
                dst_filename = artifact + ".xz"

            # Upload the file
            try:
                stored_url = storage.upload_single(
                    (upload_path, dst_filename), root_path
                )

                # Clean up compressed file if needed
                # TBD: Check if we need to keep the compressed file? Maybe
                # we dont care, pod will die anyway
                if compressed_file:
                    os.unlink(upload_path)

                print(f"[_upload_artifacts] Uploaded {artifact} to {stored_url}")
                return artifact, stored_url, None
            except Exception as e:
                print(f"[_upload_artifacts] Error uploading {artifact}: {e}")
                if compressed_file and os.path.exists(upload_path):
                    os.unlink(upload_path)
                return artifact, None, str(e)

        # Process uploads in parallel
        max_workers = min(10, len(upload_tasks))  # Limit concurrent uploads
        successful_uploads = 0
        failed_uploads = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(process_and_upload_artifact, task): task
                for task in upload_tasks
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_task):
                artifact, stored_url, error = future.result()

                if error:
                    failed_uploads.append((artifact, error))
                    continue

                successful_uploads += 1
                self._full_artifacts[artifact] = stored_url
                artifact_key = self.map_artifact_name(artifact)

                # Thread-safe update of node_af
                with node_af_lock:
                    if artifact in KERNEL_IMAGE_NAMES[self._arch]:
                        node_af['kernel'] = stored_url
                        self._node['data']['kernel_type'] = artifact.lower()
                    else:
                        node_af[artifact_key] = stored_url

        # Report results
        print(f"[_upload_artifacts] Upload complete: {successful_uploads} successful, "
              f"{len(failed_uploads)} failed")

        if failed_uploads:
            print("[_upload_artifacts] Failed uploads:")
            for artifact, error in failed_uploads:
                print(f"  - {artifact}: {error}")

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

    def submit_failure(self, message, af_uri=None):
        '''
        Submit to API that kbuild failed due internal error
        (Infrastructure failure)
        '''
        node = self._node.copy()
        node['result'] = 'incomplete'
        node['state'] = 'done'
        if 'data' not in node:
            node['data'] = {}
        node['data']['error_code'] = 'kbuild_internal_error'
        node['data']['error_msg'] = message
        # if artifacts are provided, add them to node
        if af_uri:
            node['artifacts'] = af_uri
        api = kernelci.api.get_api(self._api_config, self._api_token)
        try:
            api.node.update(node)
        except requests.exceptions.HTTPError as err:
            err_msg = json.loads(err.response.content).get("detail", [])
            print(f"[submit_failure] Error: {err_msg}")
        sys.exit(0)

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
        # retcode = 1 is build failure (fail),
        # 2 is infrastructure failure (incomplete),
        # 0 is success (pass)
        if retcode == 2:
            self.submit_failure("Infrastructure failure")
        elif retcode == 1:
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

        # do we have kselftest_tar_gz in artifact keys? then node is ok
        if self._kfselftest:
            kselftest_result = 'fail'
            for artifact in af_uri:
                if artifact == 'kselftest_tar_gz':
                    kselftest_result = 'pass'
                    break

        # This is second line of defense against kernel build failure,
        # if 'kernel' is not in artifacts, we assume it is a failure
        # but keep in mind dtbs_check can be run without kernel
        # um also special case, but need investigation
        if 'kernel' not in af_uri and not self._dtbs_check \
           and job_result == 'pass' \
           and self._arch != 'um':
            self.submit_failure("Kernel image not found in artifacts", af_uri)

        if job_result == 'pass':
            job_state = 'available'
        else:
            job_state = 'done'

        results = {
            'node': {
                'name': self._apijobname,
                'result': job_result,
                'state': job_state,
                'artifacts': af_uri,
                'holdoff': str(datetime.utcnow() + timedelta(minutes=10)),
            },
            'child_nodes': []
        }

        node = self._node.copy()
        results['node']['data'] = node['data']
        results['node']['data']['arch'] = self._arch
        results['node']['data']['compiler'] = self._compiler
        # As we are late to change data formats, we need to keep
        # defconfig as string, not list, so we use + to separate
        # multiple defconfigs
        if isinstance(self._defconfig, list):
            results['node']['data']['defconfig'] = '+'.join(self._defconfig)
        else:
            results['node']['data']['defconfig'] = self._defconfig
        results['node']['data']['fragments'] = self._fragments
        results['node']['data']['config_full'] = self._config_full

        # if we have kselftest, we need to add child node
        # but only if build was successful
        if self._kfselftest and job_result == 'pass':
            kselftest_node = self._node.copy()
            # remove id to not have same as parent
            kselftest_node.pop('id')
            kselftest_node['name'] = kselftest_node['name'] + "-kselftest"
            kselftest_node['kind'] = 'test'
            existing_path = kselftest_node.get('path')
            if existing_path and isinstance(existing_path, list):
                kselftest_node['path'] = existing_path + [kselftest_node['name']]
            kselftest_node['parent'] = self._node['id']
            kselftest_node['data'] = results['node']['data'].copy()
            kselftest_node['artifacts'] = None
            kselftest_node['state'] = 'done'
            kselftest_node['result'] = kselftest_result

            child_nodes = [
                {
                    'node': kselftest_node,
                    'child_nodes': []
                }
            ]
        else:
            child_nodes = []

        results['child_nodes'] = child_nodes
        api_helper = kernelci.api.helper.APIHelper(api)
        api_helper.submit_results(results, node)
        print(f"[_submit] submit_results to API, node: {node['id']}")
        return results
