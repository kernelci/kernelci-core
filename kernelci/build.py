# Copyright (C) 2018, 2019, 2020, 2021 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from datetime import datetime
import fnmatch
import itertools
import json
import os
import platform
import re
import shutil
import tarfile
import time
import urllib.parse

import requests
from kernelci import shell_cmd, print_flush, __version__ as kernelci_version
import kernelci.elf
import kernelci.config

# This is used to get the mainline tags as a minimum for git describe
TORVALDS_GIT_URL = \
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

CIP_CONFIG_URL = \
    "https://gitlab.com/cip-project/cip-kernel/cip-kernel-config/-\
/raw/master/{branch}/{config}"

CROS_CONFIG_URL = \
    "https://chromium.googlesource.com/chromiumos/third_party/kernel/+archive/refs/heads/{branch}/chromeos/config.tar.gz"  # noqa

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


def get_branch_head(config):
    """Get the commit SHA for the head of the branch of a given configuration

    *config* is a BuildConfig object

    The returned value is the git SHA of the current head of the branch
    associated with the build config, or None if an error occurred.
    """
    cmd = "git ls-remote {url} refs/heads/{branch}".format(
        url=config.tree.url, branch=config.branch)
    head = shell_cmd(cmd)
    if not head:
        return False
    return head.split()[0]


def _update_remote(config, path):
    shell_cmd("""
set -e
cd {path}
if git remote | grep -e '^{remote}$'; then
    git remote set-url {remote} {url}
    git remote update {remote}
    git remote prune {remote}
else
    git remote add {remote} {url}
    git remote update {remote}
fi
""".format(path=path, remote=config.tree.name, url=config.tree.url))


def _fetch_tags(path, url=TORVALDS_GIT_URL):
    shell_cmd("""
set -e
cd {path}
git fetch --tags {url}
""".format(path=path, url=url))


def update_mirror(config, path):
    """Initialise or update a local git mirror

    *config* is a BuildConfig object
    *path* is the path to the local mirror
    """
    if not os.path.exists(path):
        shell_cmd("""
set -e
mkdir -p {path}
cd {path}
git init --bare
""".format(path=path))

    _update_remote(config, path)


def clone_git(url, path, branch, shallow=True):
    """Lightweight git repo clone
    *url*  git repo url
    *path*  destination directory
    *shallow* shallow (depth=1) git clone
    """
    if not os.path.exists(path):
        shell_cmd(f"git clone {url} {path}")
    shell_cmd("""
set -e
cd {path}
git reset --hard
git clean -fd
git fetch origin
git checkout --detach origin/{branch}
""".format(path=path, branch=branch))


def update_repo(config, path, ref=None):
    """Initialise or update a local git repo

    *config* is a BuildConfig object
    *path* is the path to the local git repo
    *ref* is the path to a reference repo, typically a mirror
    """
    if not os.path.exists(path):
        ref_opt = '--reference={ref}'.format(ref=ref) if ref else ''
        shell_cmd("git clone {ref} -o {remote} {url} {path}".format(
            ref=ref_opt, remote=config.tree.name,
            url=config.tree.url, path=path))

    _update_remote(config, path)
    _fetch_tags(path, config.tree.url)
    _fetch_tags(path, TORVALDS_GIT_URL)

    shell_cmd("""
set -e
cd {path}
git reset --hard
git clean -fd
git checkout --detach {remote}/{branch}
""".format(path=path, remote=config.tree.name, branch=config.branch))


def head_commit(path):
    """Get the current git head SHA from an arbitrary git repository

    *path* is the path to the local git repository

    The returned value is the git SHA of the current HEAD of the branch checked
    out in the local git repository.
    """
    cmd = """
set -e
cd {path}
git log --pretty=format:%H -n1
""".format(path=path)
    commit = shell_cmd(cmd)
    return commit.strip()


def git_describe(tree_name, path):
    """Get the "git describe" from an arbitrary git repository

    *tree_name* is the name of the tree used in a BuildConfig
    *path* is the path to the local git repository

    The returned value is a string with the "git describe" for the commit
    currently checked out in the local git repository.
    """
    describe_args = r"--match=v\*" if tree_name == "soc" else ""
    cmd = """
set -e
cd {path}
git describe --always {describe_args}
""".format(path=path, describe_args=describe_args)
    describe = shell_cmd(cmd)
    return describe.strip().replace('/', '_')


def git_describe_verbose(path):
    """Get a verbose "git describe" from an arbitrary git repository

    *path* is the path to the local git repository

    The returned value is a string with a verbose version of "git describe" for
    the commit currently checked out in the local git repository.  This is
    typically based on a mainline kernel version tag.
    """
    cmd = r"""
set -e
cd {path}
git describe --always --match=v[1-9]\*
""".format(path=path)
    describe = shell_cmd(cmd)
    return describe.strip()


def make_tarball(kdir, tarball_name):
    """Make a kernel source tarball

    All the files in the kernel source are added to the tarball except any .git
    directory.  Note that this doesn't need to be run from within a git
    repository, any kernel source directory can be used.

    *kdir* is the path to the local kernel source directory
    *tarball_name* is the name of the tarball file to create
    """
    cwd = os.getcwd()
    os.chdir(kdir)
    _, dirs, files = next(os.walk('.'))
    with tarfile.open(os.path.join(cwd, tarball_name), 'w:gz') as tarball:
        for item in itertools.chain(dirs, files):
            tarball.add(item, filter=lambda f: f if f.name != '.git' else None)
    os.chdir(cwd)


def generate_kselftest_fragment(frag, kdir):
    """Create a config fragment file for kselftest

    *frag* is a Fragment object
    *kdir* is the path to a kernel source directory
    """
    shell_cmd(r"""
set -e
cd {kdir}
find \
  tools/testing/selftests \
  -name config \
  -printf "#\n# %h/%f\n#\n" \
  -exec cat {{}} \; \
> {frag_path}
""".format(kdir=kdir, frag_path=frag.path))
    with open(os.path.join(kdir, frag.path), 'a') as f:
        for kernel_config in frag.configs:
            f.write(kernel_config + '\n')


def generate_config_fragment(frag, kdir):
    """Generate a config fragment file for a given fragment config

    *frag* is a Fragment object
    *kdir* is the path to a kernel source directory
    """
    with open(os.path.join(kdir, frag.path), 'w') as f:
        for kernel_config in frag.configs:
            f.write(kernel_config + '\n')


def generate_fragments(config, kdir):
    """Generate all the config fragments for a given build configuration

    *config* is a BuildConfig object
    *kdir* is the path to a kernel source directory
    """
    frag_list = []
    for variant in config.variants:
        frag_list.extend(variant.fragments)
        for arch in variant.architectures:
            frag_list.extend(arch.fragments)
    for frag in frag_list:
        print(frag.path)
        if frag.name == 'kselftest':
            generate_kselftest_fragment(frag, kdir)
        elif frag.configs:
            generate_config_fragment(frag, kdir)


def _download_file(url, dest_filename, chunk_size=1024):
    headers = {
        'User-Agent': 'kernelci {}'.format(kernelci_version),
    }
    # Retry 10 times with backoff, as often nature of failure is
    # either slow network stack due load on Kubernetes node,
    # or storage server is overloaded, so backoff is necessary
    max_tries = 10
    for i in range(max_tries):
        try:
            resp = requests.get(url, stream=True, headers=headers)
            if resp.status_code == 200:
                with open(dest_filename, 'wb') as out_file:
                    for chunk in resp.iter_content(chunk_size):
                        out_file.write(chunk)
                    return True
            else:
                print(f'_download_file http code {resp.status_code}, \
retrying in {i} seconds')
                time.sleep(2*i)
                continue
        except requests.exceptions.RequestException as e:
            print(f'_download_file exception {e}, retrying in {i} seconds')
            time.sleep(2*i)
            continue

    return False


def pull_tarball(kdir, url, dest_filename, retries, delete):
    if os.path.exists(kdir):
        shutil.rmtree(kdir)
    os.makedirs(kdir)
    for i in range(1, retries + 1):
        if _download_file(url, dest_filename):
            break
        if i < retries:
            time.sleep(2 ** i)
    else:
        return False
    with tarfile.open(dest_filename, 'r:*') as tarball:
        tarball.extractall(kdir)
    if delete:
        os.remove(dest_filename)
    return True


def _get_frag_configs(kdir, frag_list):
    configs = set()
    names = set()
    for frag in frag_list:
        if os.path.exists(os.path.join(kdir, frag.path)):
            if frag.defconfig:
                configs.add(frag.defconfig)
            else:
                names.add(frag.name)
    return configs, names


def list_kernel_configs(config, kdir, single_variant=None, single_arch=None):
    """List all the kernel build combinations for a given build configuration

    List all the combinations of architecture, defconfig and compiler that are
    required to be built for a given build configuration.

    *config* is a BuildConfig object

    *kdir* is the path to the kernel source directory

    *single_variant* is an optional build variant to only list build
                     combinations that match it

    *single_arch* is an optional CPU architecture name to only list build
                  combinations that match it
    """
    kernel_configs = set()
    filter_params = {
        'kernel': git_describe_verbose(kdir),
        'tree': config.tree.name,
        'branch': config.branch,
    }

    for variant in config.variants:
        if single_variant and variant.name != single_variant:
            continue
        build_env = variant.build_environment.name
        frag_configs, frag_names = _get_frag_configs(kdir, variant.fragments)

        for arch in variant.architectures:
            if single_arch and arch.name != single_arch:
                continue
            frags = set(frag_names)
            defconfigs = set(frag_configs)
            defconfigs.add(arch.base_defconfig)
            configs, names = _get_frag_configs(kdir, arch.fragments)
            frags = frags.union(names)
            defconfigs = defconfigs.union(configs)
            for frag in frags:
                defconfigs.add('+'.join([arch.base_defconfig, frag]))
            defconfigs.update(arch.extra_configs)
            defconfigs_dir = os.path.join(kdir, 'arch', arch.name, 'configs')
            if os.path.exists(defconfigs_dir):
                for f in os.listdir(defconfigs_dir):
                    if f.endswith('defconfig'):
                        defconfigs.add(f)
            for defconfig in defconfigs:
                filter_params['defconfig'] = defconfig
                if arch.match(filter_params):
                    kernel_configs.add((arch.name, defconfig, build_env))

    return kernel_configs


class Metadata:
    """Kernel build meta-data"""

    def __init__(self, data_path, reset=False):
        """All the kernel build meta-data is read and written via this class

        *data_path* is the path to where the meta-data can be found
        *reset* is whether the meta-data should be reset in this step
        """
        self._bmeta_path = os.path.join(data_path, 'bmeta.json')
        self._steps_path = os.path.join(data_path, 'steps.json')
        self._artifacts_path = os.path.join(data_path, 'artifacts.json')
        self._bmeta = self._load_json(self._bmeta_path, dict(), reset)
        self._steps = self._load_json(self._steps_path, list(), reset)
        self._artifacts = self._load_json(self._artifacts_path, dict(), reset)
        self._artifacts_map = {
            step: {art['path']: art for art in artifacts}
            for step, artifacts in self._artifacts.items()
        }
        self._data = {
            'bmeta': self._bmeta,
            'steps': self._steps,
            'artifacts': self._artifacts,
        }

    @property
    def bmeta_path(self):
        """Path to bmeta.json"""
        return self._bmeta_path

    @property
    def steps_path(self):
        """Path to steps.json"""
        return self._steps_path

    @property
    def artifacts_path(self):
        """Path to artifacts.json"""
        return self._artifacts_path

    def _load_json(self, json_path, default, reset):
        data = default
        if os.path.exists(json_path):
            if reset:
                os.unlink(json_path)
            else:
                with open(json_path) as json_file:
                    data = json.load(json_file)
        return data

    def save(self, save_artifacts=True):
        """Save all the meta-data

        *save_artifacts* is to tell whether artifacts.json should also be saved
        """
        with open(self._bmeta_path, 'w') as json_file:
            json.dump(self._bmeta, json_file, indent=4, sort_keys=True)
        with open(self._steps_path, 'w') as json_file:
            json.dump(self._steps, json_file, indent=4, sort_keys=True)
        if save_artifacts:
            self.save_artifacts()

    def save_artifacts(self):
        """Save artifacts.json"""
        artifacts = {step: art for step, art in self._artifacts.items() if art}
        with open(self._artifacts_path, 'w') as json_file:
            json.dump(artifacts, json_file, indent=4, sort_keys=True)

    def get(self, *keys):
        """Find some meta-data value

        Without any argument, all the meta-data dictionary will be returned.
        Otherwise, each argument will be used to look up the meta-data
        recursively.  For example, to get the build status use
        `.get('bmeta', 'build', 'status')`.  If the key doesn't exist, 'None'
        is returned.

        *keys* is an arbitary number of keys to look up the meta-data
        """
        if len(keys) == 0:
            return self._data
        if len(keys) == 1:
            return self._data.get(keys[0])
        value = self._data
        for key in keys:
            value = value.get(key)
            if value is None:
                break
        return value

    def update_step(self, data):
        """Update meta-data for a build step

        Update meta-data for a build step so that if there is already a step
        with the same name, the new data overwrites the old one, otherwise the
        data is appended at the end.

        *data* is the data for the step, following the schema
        """
        for step in self._steps:
            if step['name'] == data['name']:
                step.clear()
                step.update(data)
                break
        else:
            self._steps.append(data)
        total_duration = sum(s['duration'] for s in self._steps)
        all_status = set(s['status'] for s in self._steps)
        self._bmeta['build'] = {
            'duration': total_duration,
            'status': 'PASS' if all_status == {'PASS'} else 'FAIL'
        }

    def clear_artifacts(self, step_name):
        """Delete all artifacts for a given step

        *step_name* is the name of the step for which artifact entries should
                    be removed from the meta-data
        """
        self._artifacts[step_name] = dict()

    def _add_artifact(self, step_name, artifact_type, artifact_path,
                      contents=None, key=None):
        artifacts = self._artifacts_map.setdefault(step_name, dict())
        entry = artifacts.get(artifact_path)
        if entry is None:
            entry = {
                'type': artifact_type,
                'path': artifact_path,
            }
            if key:
                entry['key'] = key
            if contents:
                entry['contents'] = list(sorted(set(contents)))
            artifacts[artifact_path] = entry
        elif entry['type'] != artifact_type:
            raise ValueError("Conflicting artifact types")
        elif entry.get('key') != key:
            raise ValueError("Conflicting artifact keys")
        self._artifacts[step_name] = list(artifacts.values())
        return entry

    def add_artifact(self, step_name, directory, file_name, key=None):
        """Add meta-data for a single artifact file

        Add a meta-data entry for a single file located in a given directory.
        The directory may be an empty string to provide a full path to the file
        directly.

        *step_name* is the name of the build step
        *directory* is the directory where the file is
        *file_name* is the name of the file within that directory
        *key* is an optional key attribute to retrieve the artifact
        """
        path = os.path.join(directory, file_name)
        return self._add_artifact(step_name, 'file', path, None, key)

    def add_artifact_contents(self, step_name, artifact_type, path,
                              contents, key=None):
        """Add meta-data for artifacts with file contents

        Add a meta-data entry for an artifact with a list of files as its
        contents.  This is typically for directories or tarballs containing
        many files.

        *step_name* is the name of the build step
        *artifact_type* is the type of artifact, typically either 'tarball' or
                       'directory'
        *path* is the path to the artifact, i.e. the path to the directory or
               tarball
        *contents* is a list of file names contained in the directory or
                   tarball
        *key* is an optional key attribute to retrieve the artifact
        """
        return self._add_artifact(
            step_name, artifact_type, path, contents, key)

    def get_single_artifact(self, step_name, key=None, attr=None):
        """Get meta-data for a single artifact

        Get the meta-data entry for a single artifact.

        *step_name* is the name of the build step
        *key* is an optional key attribute to retrieve the artifact

        *attr* is an optional attribute name to directly only get that
               attribute from the artifact meta-data (e.g. 'path'...)
        """
        artifacts = self.get('artifacts', step_name)
        if artifacts:
            if key:
                artifacts_map = {art['key']: art for art in artifacts}
                artifact = artifacts_map.get(key)
            else:
                artifact = artifacts[0]
            return artifact.get(attr) if attr and artifact else artifact
        return None


class Step:
    """Kernel build step"""

    KVER_RE = re.compile(r'^v([\d]+)\.([\d]+)')

    def __init__(self, kdir, output_path=None, log=None, reset=False):
        """Each Step deals with a part of the build and its related meta-data

        This abstract class handles the common code to run any kernel build
        step, such as running `make`, managing log files or checking whether
        some kernel config options are enabled.  It uses the `bmeta.json` file
        to share meta-data between each step and later on when sending the
        build to a database.

        Each concrete class should implement the `run()` method, with arbitrary
        arguments to perform their dedicated tasks.

        *kdir* is the path to the kernel source tree directory
        *output_path* is the path to the build output directory
        *log* is the name of the log file within the output directory, or in
              the format step-name.log where step-name is the Step.name value.
        *reset* is whether the meta-data should be reset in this step
        """
        self._kdir = kdir
        self._output_path = output_path or self.get_default_output_path(kdir)
        if not os.path.exists(self._output_path):
            os.mkdir(self._output_path)
        self._install_path = self.get_install_path(kdir, self._output_path)
        self._create_install_dir(reset)
        self._meta = Metadata(self._output_path, reset)
        self._meta.clear_artifacts(self.name)
        self._log_file = '.'.join([self.name, 'log']) if log is None else log
        self._log_path = os.path.join(self._output_path, self._log_file)
        if log is None and os.path.exists(self._log_path):
            os.unlink(self._log_path)
        self._dot_config = None
        self._start_time = time.time()

    @property
    def name(self):
        """Name of the step to use in logs and meta-data"""
        raise NotImplementedError("Step.name needs to be implemented.")

    @property
    def output_path(self):
        """Path to the kernel build output"""
        return self._output_path

    @property
    def install_path(self):
        """Path to the installation directory"""
        return self._install_path

    @classmethod
    def get_default_output_path(cls, kdir):
        """Get the default build output path based on the kernel source path

        *kdir* is the path to the kernel source directory
        """
        return os.path.join(kdir, 'build')

    @classmethod
    def get_install_path(cls, kdir=None, output_path=None):
        """Get the default build install path

        Get the default path where the kernel build artifacts get installed
        based on the kernel source tree or a supplied output path.  They are
        both optional to be able to deal with all the cases: the build output
        directory may be the default one or an arbitrary one instead.  When
        neither is supplied, the default path is `_install_` relative to the
        current working directory.

        *kdir* is the optional path to the kernel source directory
        *output_path* is the optional path to the kernel build output
        """
        if output_path is None:
            if kdir is None:
                output_path = ''
            else:
                output_path = cls.get_default_output_path(kdir)
        return os.path.join(output_path, '_install_')

    def _create_install_dir(self, reset):
        if reset:
            shutil.rmtree(self._install_path, ignore_errors=True)
        if not os.path.exists(self._install_path):
            os.makedirs(self._install_path)

    def _check_opts(self, opts, required):
        res = True
        for key in required:
            if not opts or key not in opts:
                print("Missing required option: {}".format(key))
                res = False
        return res

    def _check_min_kver(self, major, minor):
        kver = self._meta.get('bmeta', 'revision', 'describe_verbose')
        m = self.KVER_RE.match(kver)
        if m and len(m.groups()) == 2:
            k_major, k_minor = (int(g) for g in m.groups())
            return (k_major, k_minor) >= (major, minor)
        return False

    def _add_run_step(self, status, jopt=None, action=''):
        start_time = datetime.fromtimestamp(self._start_time).isoformat()
        run_data = {
            'name': ' '.join([self.name, action]) if action else self.name,
            'start_time': start_time,
            'duration': time.time() - self._start_time,
            'cpus': self._get_cpus(),
        }
        self._start_time = time.time()
        if jopt is not None:
            run_data['threads'] = str(jopt)
        if self._log_path and os.path.exists(self._log_path):
            run_data['log_file'] = self._log_file
        run_data['status'] = "PASS" if status is True else "FAIL"
        self._meta.update_step(run_data)
        self._meta.save(save_artifacts=False)
        return status

    def _get_cpus(self):
        cpus = {}
        if os.path.exists('/proc/cpuinfo'):
            cpu_list = []
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_list.append(line.split(':')[1].strip())
            for cpu in cpu_list:
                ncpus = cpus.get(cpu, 0)
                cpus[cpu] = ncpus + 1
        return cpus

    def _add_artifact(self, directory, file_name, key=None):
        return self._meta.add_artifact(self.name, directory, file_name, key)

    def _add_artifact_contents(self, artifact_type, path, contents, key=None):
        return self._meta.add_artifact_contents(
            self.name, artifact_type, path, contents, key)

    def _kernel_config_enabled(self, config_name):
        dot_config = os.path.join(self._output_path, '.config')
        cmd = 'grep -cq CONFIG_{}=y {}'.format(config_name, dot_config)
        return shell_cmd(cmd, True)

    def _kernel_config_getkey(self, opt_name):
        dot_config = os.path.join(self._output_path, '.config')
        with open(dot_config, 'r') as fp:
            for line in fp:
                if line.startswith(opt_name):
                    pcfg = line.strip().split('=')
                    if len(pcfg) > 1 and pcfg[0] == opt_name:
                        return pcfg[1]
        return None

    def _kernel_config_setkey(self, opt_name, opt_value):
        dot_config = os.path.join(self._output_path, '.config')
        cmd = f'{self._kdir}/scripts/config --file {dot_config} \
--set-str {opt_name} {opt_value}'
        return shell_cmd(cmd, True)

    def _output_to_file(self, cmd, file_path, rel_path=None):
        with open(file_path, 'a') as output_file:
            output = ["#\n"]
            if self._start_time:
                dt = datetime.fromtimestamp(time.time())
                output.append("# {}\n#\n".format(dt.isoformat()))
            output.append("# {}\n".format(cmd))
            output.append("#\n")
            output_file.write("".join(output))
        if rel_path:
            file_path = os.path.relpath(file_path, rel_path)
        cmd = "/bin/bash -c '(set -o pipefail; {} 2>&1 | tee -a {})'".format(
            cmd, file_path)
        return cmd

    def _get_make_opts(self, opts, make_path):
        env = self._meta.get('bmeta', 'environment')
        make_opts = env['make_opts'].copy()
        if opts:
            make_opts.update(opts)

        arch = env['arch']
        make_opts['ARCH'] = arch

        cc = env['compiler']
        if env['compiler'].startswith('clang'):
            make_opts['LLVM'] = '1'
        else:
            make_opts['HOSTCC'] = cc

        cross_compile = env['cross_compile']
        if cross_compile:
            make_opts['CROSS_COMPILE'] = cross_compile

        cross_compile_compat = env['cross_compile_compat']
        if cross_compile_compat:
            make_opts['CROSS_COMPILE_COMPAT'] = cross_compile_compat

        if env['use_ccache']:
            px = cross_compile if cc == 'gcc' and cross_compile else ''
            make_opts['CC'] = '"ccache {}{}"'.format(px, cc)
            ccache_dir = '-'.join(['.ccache', arch, cc])
            os.environ.setdefault('CCACHE_DIR', ccache_dir)
        elif cc != 'gcc':
            make_opts['CC'] = cc

        if self._output_path and (self._output_path != make_path):
            # due to kselftest Makefile issues, O= cannot be a relative path
            make_opts['O'] = format(os.path.abspath(self._output_path))

        return make_opts

    def _make(self, target, jopt=None, verbose=False, opts=None, subdir=None):
        make_path = os.path.join(self._kdir, subdir) if subdir else self._kdir
        make_opts = self._get_make_opts(opts, make_path)

        args = ['make']
        args += ['='.join([k, v]) for k, v in make_opts.items()]
        args += ['-C{}'.format(make_path)]

        if jopt is None:
            jopt = int(shell_cmd("nproc")) + 2
        if jopt:
            args.append('-j{}'.format(jopt))

        if not verbose:
            args.append('-s')

        if target:
            args.append(target)

        cmd = ' '.join(args)
        print_flush(cmd)
        if self._log_path:
            cmd = self._output_to_file(cmd, self._log_path)
        return shell_cmd(cmd, True)

    def _install_file(self, path, dest_dir='', dest_name=None, verbose=False):
        install_dir = os.path.join(self._install_path, dest_dir)
        if not dest_name:
            dest_name = os.path.basename(path)
        install_path = os.path.join(install_dir, dest_name)
        if verbose:
            print("Installing {}".format(install_path))
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        shutil.copy(path, install_path)
        return dest_name

    def is_enabled(self):
        """Determine whether the step is enabled with the current kernel."""
        return True

    def run(self, jopt=None, verbose=False, opts=None):
        """Abstract method to run the build step.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether to show what is being installed
        *opts* is an arbitrary dictionary with step-specific options
        """
        raise NotImplementedError("Step.run() needs to be implemented.")

    def install(self, verbose=False, status=True):
        """Base method to install the build artifacts.

        The default behaviour is to install bmeta.json and steps.json in the
        output install directory.  Sub-classes should call this parent method
        to have them installed too.

        *verbose* is whether to show what is being installed
        *status* is True if install commands succeeded, False otherwise
        """
        self._add_run_step(status, action='install')
        files = [
            (self._meta.bmeta_path, '', ''),
            (self._meta.steps_path, '', ''),
            (self._log_path, 'logs', 'log'),
        ]
        for file_name, dest_dir, key in files:
            if os.path.exists(file_name):
                item = self._install_file(file_name, dest_dir, verbose=verbose)
                if dest_dir:
                    self._add_artifact(dest_dir, item, key)
        self._meta.save_artifacts()
        self._install_file(self._meta.artifacts_path, verbose=verbose)
        return status


class RevisionData(Step):

    @property
    def name(self):
        return 'revision'

    def run(self, jopt=None, verbose=False, opts=None):
        """Add all the meta-data related to the current kernel revision.

        This step retrieves the revision information from the current kernel
        source directory using Git, typically to initialise `bmeta.json` file
        with just a revision section before running any actual build step.

        Required options in *opts*:
        *tree_name* is the short name of the kernel tree e.g. mainline, next...
        *tree_url* is the URL of the remote Git repository for the tree
        *branch* is the name of the Git branch

        Other options:
        *commit* is the Git commit checksum, if None it will be determined
                 automatically
        *describe* is the Git describe string, if None it will be determined
                   automatically
        *describe_v* is the Git describe "verbose" string, if None it will be
                     determined automatically
        """
        if not self._check_opts(opts, ('tree', 'url', 'branch')):
            return False

        revision = opts.copy()

        if not revision.get('describe'):
            revision['describe'] = git_describe(opts['tree'], self._kdir)
        if not revision.get('describe_verbose'):
            revision['describe_verbose'] = git_describe_verbose(self._kdir)
        if not revision.get('commit'):
            revision['commit'] = head_commit(self._kdir)

        self._meta.get('bmeta')['revision'] = revision

        return self._add_run_step(True)


class EnvironmentData(Step):

    @property
    def name(self):
        return 'environment'

    def run(self, jopt=None, verbose=False, opts=None):
        """Add all the meta-data related to the current build.

        This step relies on a BuildEnvironment object and also queries any
        currently installed compiler toolchain to populate the build
        environment section of the `bmeta.json` file.

        Required options in *opts*:
        *build_env* is a BuildEnvironment object
        *arch* is the CPU architecture name e.g. x86_64, arm64, riscv...
        """
        keys = ('build_env', 'arch')
        if not self._check_opts(opts, keys):
            return False

        build_env, arch = (opts[key] for key in keys)
        cross_compile, cross_compile_compat = (
            build_env.get_arch_param(arch, param) or ''
            for param in ('cross_compile', 'cross_compile_compat')
        )
        cc = build_env.cc
        cc_version_cmd = "{}{} --version 2>&1".format(
            cross_compile if cross_compile and cc == 'gcc' else '', cc)
        cc_version_full = shell_cmd(cc_version_cmd).splitlines()[0]
        make_opts = {'KBUILD_BUILD_USER': 'KernelCI'}
        make_opts.update(build_env.get_arch_param(arch, 'opts') or {})
        platform_data = {'uname': platform.uname()}

        self._meta.get('bmeta')['environment'] = {
            'arch': arch,
            'compiler': cc,
            'compiler_version': build_env.cc_version,
            'compiler_version_full': cc_version_full,
            'cross_compile': cross_compile,
            'cross_compile_compat': cross_compile_compat,
            'name': build_env.name,
            'platform': platform_data,
            'use_ccache': shell_cmd("which ccache > /dev/null", True),
            'make_opts': make_opts,
        }
        return self._add_run_step(True)


class MakeConfig(Step):

    @property
    def name(self):
        return 'config'

    def _parse_elements(self, elements):
        opts = dict()
        configs = list()
        fragments = dict()
        extras = list()

        for ele in elements:
            if ele.startswith('KCONFIG_'):
                config, value = ele.split('=')
                opts[config] = value
                extras.append(ele)
            elif ele.startswith('CONFIG_'):
                configs.append(ele)
                extras.append(ele)
            else:
                frag_path = os.path.join(self._kdir, ele)
                frag_name = os.path.basename(os.path.splitext(ele)[0])
                fragments[frag_name] = frag_path
                extras.append(frag_name)

        return opts, configs, fragments, extras

    def _expand_defconfig(self, defconfig, frags):
        split = defconfig.split('+')
        expanded = [split.pop(0)]
        for part in split:
            frag = frags.get(part)
            if frag:
                expanded.append(frag.path)
            else:
                expanded.append(part)
        return '+'.join(expanded)

    def _gen_kci_frag(self, configs, fragments, name):
        kci_frag_path = os.path.join(self._output_path, name)
        with open(kci_frag_path, 'w') as kci_frag:
            for config in configs:
                kci_frag.write(config + '\n')
            for name, path in fragments.items():
                with open(path) as frag:
                    kci_frag.write("\n# fragment from: {}\n".format(name))
                    kci_frag.writelines(frag)

    def _merge_config(self, kci_frag_name, verbose=False):
        rel_path = os.path.relpath(self._output_path, self._kdir)
        env = self._meta.get('bmeta', 'environment')
        cc = env['compiler']
        cc_env = (
            "export LLVM=1" if cc.startswith('clang') else
            "export HOSTCC={cc}\nexport CC={cc}".format(cc=cc)
        )
        cmd = """
set -e
cd {kdir}
{cc_env}
export ARCH={arch}
export CROSS_COMPILE={cross}
export CROSS_COMPILE_COMPAT={cross_compat}
export LLVM_IAS={llvm_ias}
scripts/kconfig/merge_config.sh -O {output} '{base}' '{frag}' {redir}
""".format(kdir=self._kdir, arch=env['arch'], cc_env=cc_env,
           cross=env['cross_compile'], output=rel_path,
           cross_compat=env['cross_compile_compat'],
           llvm_ias=env['make_opts'].get('LLVM_IAS', ''),
           base=os.path.join(rel_path, '.config'),
           frag=os.path.join(rel_path, kci_frag_name),
           redir='> /dev/null' if not verbose else '')
        print_flush(cmd.strip())
        if self._log_path:
            cmd = self._output_to_file(cmd, self._log_path, self._kdir)
        return shell_cmd(cmd, True)

    def _create_cip_config(self, config):
        [(branch, config)] = re.findall(r"cip://([\w\-.]+)/(.*)", config)
        cip_config = os.path.join(self._output_path, ".config")
        url = CIP_CONFIG_URL.format(branch=branch, config=config)
        if not _download_file(url, cip_config):
            raise FileNotFoundError("Error reading {}".format(url))

    def _create_cros_config(self, config):
        [(branch, config)] = re.findall(r"cros://([\w\-.]+)/(.*)", config)
        cros_config = os.path.join(self._output_path, "cros-config.tgz")
        url = CROS_CONFIG_URL.format(branch=branch)
        if not _download_file(url, cros_config):
            raise FileNotFoundError("Error reading {}".format(url))
        tar = tarfile.open(cros_config)
        subdir = 'chromeos'
        with open(os.path.join(self._output_path, ".config"), 'wb') as f:
            config_file_names = [
                os.path.join(subdir, 'base.config'),
                os.path.join(subdir, os.path.dirname(config), "common.config"),
                os.path.join(subdir, config),
            ]
            for file_name in config_file_names:
                f.write(tar.extractfile(file_name).read())

    def run(self, jopt=None, verbose=False, opts=None):
        """Make the kernel config

        Make the kernel .config file using a number of options.  This will
        first use a given defconfig, then use the KernelCI extended syntax for
        enabling or disabling any extra kernel build options defined or merge
        any config fragment files.  Finally it will save the extra config
        options in a separate config fragment called `kernelci.config` by
        default.  The "kernel" section in `bmeta.json` will be created with the
        defconfig name and other related meta-data about extra config options
        and fragments.

        Required options in *opts*:
        *defconfig* is the defconfig name, e.g. defconfig, x86_64_defconfig...
        *frags_config* is a dict with the Fragment configuration objects
        """
        keys = ('defconfig', 'frags_config')
        if not self._check_opts(opts, keys):
            return False

        defconfig, frags_config = (opts[key] for key in keys)
        defconfig_expanded = self._expand_defconfig(defconfig, frags_config)
        elements = defconfig_expanded.split('+')
        target = elements.pop(0)
        kci_frag_name = None
        opts, configs, fragments, extras = self._parse_elements(elements)

        if configs or fragments:
            kci_frag_name = 'kernelci.config'
            self._gen_kci_frag(configs, fragments, kci_frag_name)

        bmeta = self._meta.get('bmeta')
        rev, env = (bmeta[cat] for cat in ('revision', 'environment'))
        publish_path = '/'.join((
            re.sub(r'[\/:]', '-', item) for item in [
                rev['tree'],
                rev['branch'],
                rev['describe'],
                env['arch'],
                defconfig,
                env['name'],
            ])
        )

        bmeta['kernel'] = {
            'defconfig': target,
            'defconfig_full': defconfig,
            'defconfig_expanded': defconfig_expanded,
            'defconfig_extras': extras,
            'publish_path': publish_path,
        }

        if target.startswith("cip://"):
            self._create_cip_config(target)
            res = self._make('olddefconfig', jopt, verbose, opts)
        elif target.startswith("cros://"):
            self._create_cros_config(target)
            res = self._make('olddefconfig', jopt, verbose, opts)
        else:
            res = self._make(target, jopt, verbose, opts)

        if res and kci_frag_name:
            # ToDo: treat kernelci.config as an implementation detail and list
            # the actual input config fragment files here instead
            bmeta['kernel']['fragments'] = [kci_frag_name]
            res = self._merge_config(kci_frag_name, verbose)

        return self._add_run_step(res, jopt)

    def install(self, verbose=False):
        """Install the kernel configuration files

        Install the Linux kernel config file and associated fragments.

        *verbose* is whether the build output should be shown
        """
        item = self._install_file(
            os.path.join(self._output_path, '.config'), 'config',
            'kernel.config', verbose
        )
        self._add_artifact('config', item, 'config')
        for frag in self._meta.get('bmeta', 'kernel').get('fragments', list()):
            item = self._install_file(
                os.path.join(self._output_path, frag), 'config', frag, verbose
            )
            self._add_artifact('config', item, 'fragment')
        return super().install(verbose)


class FetchFirmware(Step):

    @property
    def name(self):
        return 'firmware'

    def run(self, jopt=None, verbose=False, opts=None):
        """Fetch linux-firmware repository

        If kernel have CONFIG_EXTRA_FIRMWARE enabled we need to fetch
        fresh snapshot of linux-firmware git repository, otherwise
        kernel will not be able to build
        """
        # CONFIG_EXTRA_FIRMWARE_DIR need absolute path
        full_path = os.path.abspath(self._output_path)
        fwdir = os.path.join(full_path, 'linux-firmware')
        fwfiles = os.path.join(full_path, 'firmware-files')
        key = self._kernel_config_getkey('CONFIG_EXTRA_FIRMWARE')
        if key and key == '""':
            if verbose:
                print("External firmware not required")
            return self._add_run_step(True)
        if verbose:
            print("Fetching firmware")
        repourl = 'git://git.kernel.org/pub/scm/linux/kernel/git/\
firmware/linux-firmware.git'
        clone_git(repourl, fwdir, 'main')
        # We need to extract files and symlinks using copy-firmware.sh
        shell_cmd(f"rm -rf {fwfiles} && mkdir {fwfiles}")
        shell_cmd(f"cd {fwdir} && ./copy-firmware.sh {fwfiles} && cd -")
        # We need to override directory where firmware stored
        self._kernel_config_setkey('CONFIG_EXTRA_FIRMWARE_DIR',
                                   f'"{fwfiles}"')
        bmeta = self._meta.get('bmeta')
        fbmeta = bmeta.setdefault('firmware', dict())
        fbmeta['commit'] = kernelci.build.head_commit(fwdir)

        return self._add_run_step(True)


class MakeKernel(Step):

    @property
    def name(self):
        return 'kernel'

    def run(self, jopt=None, verbose=False, opts=None):
        """Make the kernel image

        Make the actual kernel image given the parameters already provided in
        previous steps via `bmeta.json`.  This will also add some meta-data
        such as the kernel image name and ELF properties.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        bmeta = self._meta.get('bmeta')
        if self._kernel_config_enabled('XIP_KERNEL'):
            target = 'xipImage'
        elif self._kernel_config_enabled('SYS_SUPPORTS_ZBOOT'):
            target = 'vmlinuz'
        else:
            target = MAKE_TARGETS.get(bmeta['environment']['arch'])

        kbmeta = bmeta.setdefault('kernel', dict())
        if target:
            kbmeta['image'] = target

        if self._kernel_config_enabled('CPU_BIG_ENDIAN'):
            kbmeta['endianness'] = 'big'
        else:
            kbmeta['endianness'] = 'little'

        res = self._make(target, jopt, verbose)

        if res:
            vmlinux_file = os.path.join(self._output_path, 'vmlinux')
            if os.path.isfile(vmlinux_file):
                vmlinux_meta = kernelci.elf.read(vmlinux_file)
                kbmeta.update(vmlinux_meta)
                kbmeta['vmlinux_file_size'] = os.stat(vmlinux_file).st_size

        return self._add_run_step(res, jopt)

    def _find_kernel_images(self, image):
        arch = self._meta.get('bmeta', 'environment', 'arch')
        kimage_names = KERNEL_IMAGE_NAMES[arch]
        kimages = dict()

        if image:
            kimage_names.add(image)

        image_paths = [
            os.path.join(self._output_path, 'arch', arch, 'boot'),
            self._output_path
        ]

        for path in (p for p in image_paths if os.path.isdir(p)):
            files = set(os.listdir(path))
            image_files = files.intersection(kimage_names)
            kimages.update({im: os.path.join(path, im) for im in image_files})

        return kimages

    def _install_system_map(self, kbmeta, verbose):
        file_name = 'System.map'
        system_map = os.path.join(self._output_path, file_name)
        if os.path.exists(system_map):
            text = shell_cmd('grep " _text" {}'.format(system_map)).split()[0]
            text_offset = int(text, 16) & (1 << 30)-1  # phys: cap at 1G
            item = self._install_file(system_map, 'kernel', file_name, verbose)
            self._add_artifact('kernel', file_name, 'system_map')
            kbmeta['text_offset'] = '0x{:08x}'.format(text_offset)

    def install(self, verbose=False):
        """Install the kernel image

        Install the Linux kernel image as well as System.map.

        *verbose* is whether the build output should be shown
        """
        kbmeta = self._meta.get('bmeta', 'kernel')
        image = kbmeta.get('image')
        kimages = self._find_kernel_images(image)
        res = bool(kimages)

        if not res:
            print_flush("No kernel image found")
        else:
            self._install_system_map(kbmeta, verbose)
            if image not in kimages:
                image = sorted(kimages.keys())[0]
                kbmeta['image'] = image
            self._install_file(kimages[image], 'kernel', image, verbose)
            self._add_artifact('kernel', image, 'image')

        return super().install(verbose, res)


class MakeModules(Step):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mod_path = os.path.join(self._output_path, '_modules_')

    @property
    def name(self):
        return 'modules'

    def is_enabled(self):
        """Check whether modules are enabled.

        Return True if the modules are enabled in the kernel config file, or
        False otherwise.  This can be used to determine whether the step should
        be run or not, prior to running it.
        """
        return self._kernel_config_enabled('MODULES')

    def run(self, jopt=None, verbose=False, opts=None):
        """Make the kernel modules

        Make the kernel modules and   This step does not add any extra build
        meta-data.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        res = self._make('modules', jopt, verbose)
        return self._add_run_step(res, jopt)

    def _make_modules_install(self, jopt, verbose):
        if os.path.exists(self._mod_path):
            shutil.rmtree(self._mod_path)
        os.makedirs(self._mod_path)
        cross_compile = self._meta.get('bmeta', 'environment', 'cross_compile')
        opts = {
            'INSTALL_MOD_PATH': os.path.abspath(self._mod_path),
            'INSTALL_MOD_STRIP': '1',
            'STRIP': "{}strip".format(cross_compile),
        }
        return self._make('modules_install', jopt, verbose, opts)

    def _get_modules_artifacts(self, modules_tarball):
        with tarfile.open(modules_tarball, 'r:xz') as tarball:
            modules = sorted(list(set(
                path for path in (
                    os.path.basename(entry.name)
                    for entry in tarball
                )
                if path and path.endswith('.ko')
            )))
        return modules

    def _create_modules_tarball(self, verbose, modules_tarball, compr='J'):
        modules_tarball_path = os.path.join(
            self._install_path, modules_tarball)
        if verbose:
            print("Creating {}".format(modules_tarball_path))
        shell_cmd("tar -C{path} -c{compr}f {tarball} .".format(
            path=self._mod_path, compr=compr, tarball=modules_tarball_path))
        return modules_tarball_path

    def install(self, verbose=False, jopt=None):
        """Install the kernel modules

        Install the kernel modules as stripped binaries in a _modules_ build
        sub-directory.  Also install a tarball with all the module files and
        list all the files as artifacts.

        *verbose* is whether the build output should be shown
        *jopt* is the `make -j` option which will default to `nproc + 2`
        """
        res = self._make_modules_install(jopt, verbose)

        if res:
            tarball = 'modules.tar.xz'
            tarball_path = self._create_modules_tarball(verbose, tarball)
            modules = self._get_modules_artifacts(tarball_path)
            self._add_artifact_contents('tarball', tarball, modules)

        return super().install(verbose, res)


class MakeDeviceTrees(Step):

    @property
    def name(self):
        return 'dtbs'

    def is_enabled(self):
        """Check whether device tree support is enabled.

        Return True if device tree support is enabled in the kernel config, or
        False otherwise.  This can be used to not run this step and skip
        building dtbs if they are not supported.
        """
        return self._kernel_config_enabled('OF_FLATTREE')

    def run(self, jopt=None, verbose=False, opts=None):
        """Make the device trees

        Make the device tree binary files (dtbs).  This step does not add any
        extra build meta-data.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        res = self._make('dtbs', jopt, verbose)
        return self._add_run_step(res, jopt)

    def _install_dtbs(self, verbose):
        arch = self._meta.get('bmeta', 'environment', 'arch')
        boot_dir = os.path.join(self._output_path, 'arch', arch, 'boot')
        dts_dir = os.path.join(boot_dir, 'dts')
        dtb_list = []

        dtbs_path = os.path.join(self._install_path, 'dtbs')
        if os.path.exists(dtbs_path):
            shutil.rmtree(dtbs_path)

        if verbose:
            print("Copying dtbs to {}".format(dtbs_path))

        for root, _, files in os.walk(dts_dir):
            for f in fnmatch.filter(files, '*.dtb'):
                dtb_path = os.path.join(root, f)
                dtb_rel = os.path.relpath(dtb_path, dts_dir)
                dtb_list.append(dtb_rel)
                dest_path = os.path.join(dtbs_path, dtb_rel)
                dest_dir = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy(dtb_path, dest_path)

        return dtb_list

    def install(self, verbose=False):
        """Install the device trees

        Install the device tree binary blobs (dtbs) and list all the .dtb files
        in artifacts.

        *verbose* is whether the build output should be shown
        """
        dtb_list = self._install_dtbs(verbose)
        self._add_artifact_contents('directory', 'dtbs', dtb_list)
        return super().install(verbose)


class MakeSelftests(Step):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return 'kselftest'

    def is_enabled(self):
        """Check whether the kselftest fragment is enabled

        Return True if the kselftest config fragment is enabled in the build
        meta-data, or False otherwise.
        """
        return self._check_min_kver(5, 10)

    def run(self, jopt=None, verbose=False, opts=None):
        """Make the kernel selftests

        Make the kernel selftests or "kselftest" and produce a tarball so they
        can be installed on a separate test platform.  This step does not add
        any extrabuild meta-data.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        opts = {
            'FORMAT': '.xz',
        }
        if self._check_min_kver(5, 20):
            # Once v5.20 has been released and a new LTS has been declared then
            # we can always run this command and bump the v5.10 version test
            # for kselftest altogether.
            res = self._make('kselftest-gen_tar', jopt, verbose, opts)
        else:
            res = self._make('headers', jopt, verbose)
            if res:
                res = self._make('gen_tar', jopt, verbose, opts,
                                 'tools/testing/selftests')
        return self._add_run_step(res, jopt)

    def _get_kselftests(self, kselftest_tarball):
        with tarfile.open(kselftest_tarball, 'r:xz') as tarball:
            kselftests = set(
                path for path in (
                    os.path.split(os.path.relpath(entry.name))[0]
                    for entry in tarball
                )
                if path
            )
        return kselftests

    def install(self, verbose=False):
        """Install the kselftest tarball

        Install the kselftest tarball which was already packaged as part of the
        build action.

        *verbose* is whether the build output should be shown
        """
        kselftest_tarball = os.path.join(
            self._output_path,
            'kselftest/kselftest_install/kselftest-packages/kselftest.tar.xz'
        )

        res = os.path.exists(kselftest_tarball)
        if res:
            tarball = self._install_file(kselftest_tarball, verbose=verbose)
            kselftests = self._get_kselftests(kselftest_tarball)
            self._add_artifact_contents('tarball', tarball, kselftests)

        return super().install(verbose, res)
