# Copyright (C) 2018, 2019, 2020 Collabora Limited
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
import requests
import shutil
import stat
import tarfile
import tempfile
import time
import urllib.parse

from kernelci import shell_cmd, print_flush
import kernelci.elf
from kernelci.storage import upload_files

# This is used to get the mainline tags as a minimum for git describe
TORVALDS_GIT_URL = \
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

# Hard-coded make targets for each CPU architecture
MAKE_TARGETS = {
    'arm': 'zImage',
    'arm64': 'Image',
    'arc': 'uImage',
    'i386': 'bzImage',
    'x86_64': 'bzImage',
}

# Hard-coded binary kernel image names for each CPU architecture
KERNEL_IMAGE_NAMES = {
    'arm': {'zImage', 'xipImage'},
    'arm64': {'Image'},
    'arc': {'uImage'},
    'i386': {'bzImage'},
    'mips': {'uImage.gz', 'vmlinux.gz.itb', 'vmlinuz'},
    'riscv': {'Image', 'Image.gz'},
    'x86_64': {'bzImage'},
    'x86': {'bzImage'},
}


def _get_last_commit_file_name(config):
    return '_'.join(['last-commit', config.name])


def get_last_commit(config, storage):
    """Get the last commit SHA that was built for a given build configuration

    *config* is a BuildConfig object
    *storage* is the base URL for the storage server

    The returned value is the SHA of the last git commit that was built, or
    None if an error occurred or if the configuration has never been built.
    """
    last_commit_url = "{storage}/{tree}/{file_name}".format(
        storage=storage, tree=config.tree.name,
        file_name=_get_last_commit_file_name(config))
    last_commit_resp = requests.get(last_commit_url)
    if last_commit_resp.status_code != 200:
        return False
    return last_commit_resp.text.strip()


def set_last_commit(config, api, token, commit):
    """Set the last commit SHA that was built for a given build configuration

    *config* is a BuildConfig object
    *api* is the URL of the KernelCI backend API
    *token* is the backend API token to use
    *commit* is the git SHA to send
    """
    upload_files(api, token, config.tree.name,
                 {_get_last_commit_file_name(config): commit})


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


def check_new_commit(config, storage):
    """Check if there is a new commit that hasn't been built yet

    *config* is a BuildConfig object
    *storage* is the base URL of the storage server

    The returned value is the git SHA of a new commit to be built if there is
    one, or True if the last built commit is the same as the branch head
    (nothing to do), or False if an error occurred.
    """
    last_commit = get_last_commit(config, storage)
    branch_head = get_branch_head(config)
    if not branch_head:
        return False
    elif last_commit == branch_head:
        return True
    else:
        return branch_head


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


def add_kselftest_fragment(path, frag_path='kernel/configs/kselftest.config'):
    """Create a config fragment file for kselftest

    *path* is the path to the local kernel git repository
    *frag_path* is the path where to create the fragment within the repo
    """
    shell_cmd(r"""
set -e
cd {path}
find \
  tools/testing/selftests \
  -name config \
  -printf "#\n# %h/%f\n#\n" \
  -exec cat {{}} \; \
> {frag_path}
""".format(path=path, frag_path=frag_path))


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
            add_kselftest_fragment(kdir)
        elif frag.configs:
            generate_config_fragment(frag, kdir)


def push_tarball(config, kdir, storage, api, token):
    """Create and push a linux kernel source tarball to the storage server

    If a tarball with a same name is already on the storage server, no new
    tarball is uploaded.  Otherwise, a tarball is created

    *config* is a BuildConfig object
    *kdir* is the path to a kernel source directory
    *storage* is the base URL of the storage server
    *api* is the URL of the KernelCI backend API
    *token* is the token to use with the KernelCI backend API

    The returned value is the URL of the uploaded tarball.
    """
    tarball_name = "linux-src_{}.tar.gz".format(config.name)
    describe = git_describe(config.tree.name, kdir)
    path = '/'.join(list(item.replace('/', '-') for item in [
        config.tree.name, config.branch, describe
    ]))
    tarball_url = urllib.parse.urljoin(storage, '/'.join([path, tarball_name]))
    resp = requests.head(tarball_url)
    if resp.status_code == 200:
        return tarball_url
    tarball = "{}.tar.gz".format(config.name)
    make_tarball(kdir, tarball)
    upload_files(api, token, path, {tarball_name: open(tarball, 'rb')})
    os.unlink(tarball)
    return tarball_url


def _download_file(url, dest_filename, chunk_size=1024):
    resp = requests.get(url, stream=True)
    if resp.status_code == 200:
        with open(dest_filename, 'wb') as out_file:
            for chunk in resp.iter_content(chunk_size):
                out_file.write(chunk)
        return True
    else:
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


def _add_frag_configs(kdir, frag_list, frag_paths, frag_configs):
    for frag in frag_list:
        if os.path.exists(os.path.join(kdir, frag.path)):
            if frag.defconfig:
                frag_configs.add(frag.defconfig)
            else:
                frag_paths.add(frag.path)


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
        frag_paths = set()
        frag_configs = set()
        _add_frag_configs(kdir, variant.fragments, frag_paths, frag_configs)
        for arch in variant.architectures:
            if single_arch and arch.name != single_arch:
                continue
            frags = set(frag_paths)
            defconfigs = set(frag_configs)
            defconfigs.add(arch.base_defconfig)
            _add_frag_configs(kdir, arch.fragments, frags, defconfigs)
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


def _output_to_file(cmd, log_file, rel_dir=None):
    open(log_file, 'a').write("#\n# {}\n#\n".format(cmd))
    if rel_dir:
        log_file = os.path.relpath(log_file, rel_dir)
    cmd = "/bin/bash -c '(set -o pipefail; {} 2>&1 | tee -a {})'".format(
        cmd, log_file)
    return cmd


def _run_make(kdir, arch, target=None, jopt=None, silent=True, cc='gcc',
              cross_compile=None, use_ccache=None, output=None, log_file=None,
              opts=None, cross_compile_compat=None):
    args = ['make']

    if opts:
        args += ['='.join([k, v]) for k, v in opts.items()]

    args += ['-C{}'.format(kdir)]

    if jopt:
        args.append('-j{}'.format(jopt))

    if silent:
        args.append('-s')

    args.append('ARCH={}'.format(arch))

    if cross_compile:
        args.append('CROSS_COMPILE={}'.format(cross_compile))

    if cross_compile_compat:
        args.append('CROSS_COMPILE_COMPAT={}'.format(cross_compile_compat))

    if cc.startswith('clang'):
        args.append('LLVM=1')
    else:
        args.append('HOSTCC={}'.format(cc))

    if use_ccache:
        px = cross_compile if cc == 'gcc' and cross_compile else ''
        args.append('CC="ccache {}{}"'.format(px, cc))
        ccache_dir = '-'.join(['.ccache', arch, cc])
        os.environ.setdefault('CCACHE_DIR', ccache_dir)
    elif cc != 'gcc':
        args.append('CC={}'.format(cc))

    if output != kdir:
        # due to kselftest Makefile issues, O= cannot be a relative path
        args.append('O={}'.format(os.path.abspath(output)))

    if target:
        args.append(target)

    cmd = ' '.join(args)
    print_flush(cmd)
    if log_file:
        cmd = _output_to_file(cmd, log_file)
    return shell_cmd(cmd, True)


class Step:
    """Kernel build step"""

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
        self._reset = reset
        self._output_path = output_path or os.path.join(kdir, 'build')
        if not os.path.exists(self._output_path):
            os.mkdir(self._output_path)
        self._install_path = os.path.join(self._output_path, '_install_')
        self._create_install_dir()
        self._bmeta_path = os.path.join(self._output_path, 'bmeta.json')
        self._steps_path = os.path.join(self._output_path, 'steps.json')
        self._bmeta = self._load_json(self._bmeta_path, dict())
        self._steps = self._load_json(self._steps_path, list())
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
    def install_path(self):
        """Path to the installation directory"""
        return self._install_path

    def _load_json(self, json_path, default):
        data = default
        if os.path.exists(json_path):
            if self._reset:
                os.unlink(json_path)
            else:
                with open(json_path) as json_file:
                    data = json.load(json_file)
        return data

    def _save_bmeta(self):
        with open(self._bmeta_path, 'w') as json_file:
            json.dump(self._bmeta, json_file, indent=4, sort_keys=True)
        with open(self._steps_path, 'w') as json_file:
            json.dump(self._steps, json_file, indent=4, sort_keys=True)

    def _create_install_dir(self):
        if self._reset:
            shutil.rmtree(self._install_path, ignore_errors=True)
        if not os.path.exists(self._install_path):
            os.makedirs(self._install_path)

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
        self._steps.append(run_data)

        total_duration = sum(s['duration'] for s in self._steps)
        all_status = set(s['status'] for s in self._steps)
        self._bmeta['build'] = {
            'duration': total_duration,
            'status': 'PASS' if all_status == {'PASS'} else 'FAIL'
        }
        self._save_bmeta()
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

    def _kernel_config_enabled(self, config_name):
        dot_config = os.path.join(self._output_path, '.config')
        cmd = 'grep -cq CONFIG_{}=y {}'.format(config_name, dot_config)
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
        env = self._bmeta['environment']
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

    def is_enabled(self):
        """Determine whether the step is enabled with the current kernel."""
        return True

    def run(self):
        """Abstract method to run the build step."""
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
            (self._bmeta_path, ''),
            (self._steps_path, ''),
            (self._log_path, 'logs'),
        ]
        for file_name, dest_dir in files:
            if os.path.exists(file_name):
                self._install_file(file_name, dest_dir, verbose=verbose)
        return status


class RevisionData(Step):

    @property
    def name(self):
        return 'revision'

    def run(self, tree_name, tree_url, branch):
        """Add all the meta-data related to the current kernel revision.

        This step retrieves the revision information from the current kernel
        source directory using Git, typically to initialise `bmeta.json` file
        with just a revision section before running any actual build step.

        *tree_name* is the short name of the kernel tree e.g. mainline, next...
        *tree_url* is the URL of the remote Git repository for the tree
        *branch* is the name of the Git branch
        """
        self._bmeta['revision'] = {
            'tree': tree_name,
            'url': tree_url,
            'branch': branch,
            'describe': git_describe(tree_name, self._kdir),
            'describe_v': git_describe_verbose(self._kdir),
            'commit': head_commit(self._kdir),
        }
        return self._add_run_step(True)


class EnvironmentData(Step):

    @property
    def name(self):
        return 'environment'

    def run(self, build_env, arch):
        """Add all the meta-data related to the current build.

        This step relies on a BuildEnvironment object and also queries any
        currently installed compiler toolchain to populate the build
        environment section of the `bmeta.json` file.

        *build_env* is a BuildEnvironment object
        *arch* is the CPU architecture name e.g. x86_64, arm64, riscv...
        """
        cross_compile = build_env.get_cross_compile(arch) or ''
        cross_compile_compat = build_env.get_cross_compile_compat(arch) or ''
        cc = build_env.cc
        cc_version_cmd = "{}{} --version 2>&1".format(
            cross_compile if cross_compile and cc == 'gcc' else '', cc)
        cc_version_full = shell_cmd(cc_version_cmd).splitlines()[0]
        make_opts = {'KBUILD_BUILD_USER': 'KernelCI'}
        make_opts.update(build_env.get_arch_opts(arch))
        platform_data = {'uname': platform.uname()}

        self._bmeta['environment'] = {
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
        env = self._bmeta['environment']
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

    def run(self, defconfig, jopt=None, verbose=False, frag='kernelci.config'):
        """Make the kernel config

        Make the kernel .config file using a number of options.  This will
        first use a given defconfig, then use the KernelCI extended syntax for
        enabling or disabling any extra kernel build options defined or merge
        any config fragment files.  Finally it will save the extra config
        options in a separate config fragment called `kernelci.config` by
        default.  The "kernel" section in `bmeta.json` will be created with the
        defconfig name and other related meta-data about extra config options
        and fragments.

        *defconfig* is the defconfig name, e.g. defconfig, x86_64_defconfig...
        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        *frag* is the name of the output kernel config fragment
        """
        elements = defconfig.split('+')
        target = elements.pop(0)
        kci_frag_name = None
        opts, configs, fragments, extras = self._parse_elements(elements)

        if configs or fragments:
            kci_frag_name = frag
            self._gen_kci_frag(configs, fragments, kci_frag_name)

        self._bmeta['kernel'] = {
            'defconfig': target,
            'defconfig_full': defconfig,
            'defconfig_extras': extras,
        }

        res = self._make(target, jopt, verbose, opts)

        if res and kci_frag_name:
            # ToDo: treat kernelci.config as an implementation detail and list
            # the actual input config fragment files here instead
            self._bmeta['kernel']['fragments'] = [kci_frag_name]
            res = self._merge_config(kci_frag_name, verbose)

        return self._add_run_step(res, jopt)

    def install(self, verbose=False):
        """Install the kernel configuration files

        Install the Linux kernel config file and associated fragments.

        *verbose* is whether the build output should be shown
        """
        self._install_file(
            os.path.join(self._output_path, '.config'), 'config',
            'kernel.config', verbose
        )
        for frag in self._bmeta['kernel'].get('fragments', list()):
            self._install_file(
                os.path.join(self._output_path, frag), 'config', frag, verbose
            )
        return super().install(verbose)


class MakeKernel(Step):

    @property
    def name(self):
        return 'kernel'

    def run(self, jopt=None, verbose=False):
        """Make the kernel image

        Make the actual kernel image given the parameters already provided in
        previous steps via `bmeta.json`.  This will also add some meta-data
        such as the kernel image name and ELF properties.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        if self._kernel_config_enabled('XIP_KERNEL'):
            target = 'xipImage'
        elif self._kernel_config_enabled('SYS_SUPPORTS_ZBOOT'):
            target = 'vmlinuz'
        else:
            target = MAKE_TARGETS.get(self._bmeta['environment']['arch'])

        kbmeta = self._bmeta.setdefault('kernel', dict())
        if target:
            kbmeta['image'] = target

        res = self._make(target, jopt, verbose)

        if res:
            vmlinux_file = os.path.join(self._output_path, 'vmlinux')
            if os.path.isfile(vmlinux_file):
                vmlinux_meta = kernelci.elf.read(vmlinux_file)
                kbmeta.update(vmlinux_meta)
                kbmeta['vmlinux_file_size'] = os.stat(vmlinux_file).st_size

        return self._add_run_step(res, jopt)

    def _find_kernel_images(self, image):
        arch = self._bmeta['environment']['arch']
        boot_dir = os.path.join(self._output_path, 'arch', arch, 'boot')
        kimage_names = KERNEL_IMAGE_NAMES[arch]
        kimages = dict()

        if image:
            kimage_names.add(image)

        for path in boot_dir, self._output_path:
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
            self._install_file(system_map, 'kernel', file_name, verbose)
            kbmeta.update({
                'system_map': file_name,
                'text_offset': '0x{:08x}'.format(text_offset),
            })

    def install(self, verbose=False):
        """Install the kernel image

        Install the Linux kernel image as well as System.map.

        *verbose* is whether the build output should be shown
        """
        kbmeta = self._bmeta['kernel']
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

    def _make_modules_install(self, jopt, verbose):
        if os.path.exists(self._mod_path):
            shutil.rmtree(self._mod_path)
        os.makedirs(self._mod_path)
        cross_compile = self._bmeta['environment']['cross_compile']
        opts = {
            'INSTALL_MOD_PATH': os.path.abspath(self._mod_path),
            'INSTALL_MOD_STRIP': '1',
            'STRIP': "{}strip".format(cross_compile),
        }
        return self._make('modules_install', jopt, verbose, opts)

    def _create_modules_json(self, verbose):
        mod_json = os.path.join(self._install_path, 'modules.json')
        if verbose:
            print("Creating {}".format(mod_json))
        modules = []
        for root, _, files in os.walk(self._mod_path):
            rel_path = os.path.relpath(self._kdir)
            for fname in fnmatch.filter(files, '*.ko'):
                module_path = os.path.join(rel_path, fname)
                modules.append(module_path)
        with open(mod_json, 'w') as json_file:
            json.dump({'modules': sorted(modules)}, json_file, indent=4)

    def _create_modules_tarball(self, verbose):
        modules_tarball = 'modules.tar.xz'
        modules_tarball_path = os.path.join(
            self._install_path, modules_tarball)
        if verbose:
            print("Creating {}".format(modules_tarball_path))
        shell_cmd("tar -C{path} -cJf {tarball} .".format(
            path=self._mod_path, tarball=modules_tarball_path))

    def run(self, jopt=None, verbose=False):
        """Make the kernel modules

        Make the kernel modules and   This step does not add any extra build
        meta-data.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        res = self._make('modules', jopt, verbose)
        return self._add_run_step(res, jopt)

    def install(self, verbose=False, jopt=None):
        """Install the kernel modules

        Install the kernel modules as stripped binaries in a _modules_ output
        sub-directory.  Also create a modules.json file with the list of all
        the module files and a tarball with all the modules.

        *verbose* is whether the build output should be shown
        *jopt* is the `make -j` option which will default to `nproc + 2`
        """
        res = self._make_modules_install(jopt, verbose)

        if res:
            self._create_modules_json(verbose)
            self._create_modules_tarball(verbose)

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

    def run(self, jopt=None, verbose=False):
        """Make the device trees

        Make the device tree binary files (dtbs).  This step does not add any
        extra build meta-data.

        *jopt* is the `make -j` option which will default to `nproc + 2`
        *verbose* is whether the build output should be shown
        """
        res = self._make('dtbs', jopt, verbose)
        return self._add_run_step(res, jopt)

    def _install_dtbs(self, verbose):
        arch = self._bmeta['environment']['arch']
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

    def _create_dtbs_json(self, dtb_list, verbose):
        dtbs_json = os.path.join(self._install_path, 'dtbs.json')
        if verbose:
            print("Creating {}".format(dtbs_json))
        with open(dtbs_json, 'w') as json_file:
            json.dump({'dtbs': sorted(dtb_list)}, json_file, indent=4)

    def install(self, verbose=False):
        """Install the device trees

        Install the device tree binary blobs (dtbs) and generate dtbs.json with
        the list of device tree files.

        *verbose* is whether the build output should be shown
        """
        dtb_list = self._install_dtbs(verbose)
        self._create_dtbs_json(dtb_list, verbose)
        return super().install(verbose)


class MakeSelftests(Step):

    @property
    def name(self):
        return 'kselftest'

    def is_enabled(self):
        """Check whether the kselftest fragment is enabled

        Return True if the kselftest config fragment is enabled in the build
        meta-data, or False otherwise.
        """
        return 'kselftest' in self._bmeta['kernel']['defconfig_extras']

    def run(self, jopt=None, verbose=False):
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
        res = self._make('gen_tar', jopt, verbose, opts,
                         'tools/testing/selftests')
        return self._add_run_step(jopt, res)

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
            self._install_file(kselftest_tarball, verbose=verbose)

        return super().install(verbose, res)


def _make_defconfig(defconfig, kwargs, extras, verbose, log_file):
    kdir, output_path = (kwargs.get(k) for k in ('kdir', 'output'))
    result = True

    defconfig_kwargs = dict(kwargs)
    defconfig_opts = dict(defconfig_kwargs['opts'])
    defconfig_kwargs['opts'] = defconfig_opts
    tmpfile_fd, tmpfile_path = tempfile.mkstemp(prefix='kconfig-')
    tmpfile = os.fdopen(tmpfile_fd, 'w')
    tmpfile_used = False
    defs = defconfig.split('+')
    target = defs.pop(0)
    for d in defs:
        if d.startswith('KCONFIG_'):
            config, value = d.split('=')
            defconfig_opts[config] = value
            extras.append(d)
        elif d.startswith('CONFIG_'):
            tmpfile.write(d + '\n')
            extras.append(d)
            tmpfile_used = True
        else:
            frag_path = os.path.join(kdir, d)
            if os.path.exists(frag_path):
                with open(frag_path) as frag:
                    tmpfile.write("\n# fragment from : {}\n".format(d))
                    tmpfile.writelines(frag)
                    tmpfile_used = True
                extras.append(os.path.basename(os.path.splitext(d)[0]))
            else:
                print_flush("Fragment not found: {}".format(frag_path))
                result = False
    tmpfile.flush()

    if not _run_make(target=target, **defconfig_kwargs):
        result = False

    if result and tmpfile_used:
        kconfig_frag_name = 'frag.config'
        kconfig_frag = os.path.join(output_path, kconfig_frag_name)
        shutil.copy(tmpfile_path, kconfig_frag)
        os.chmod(kconfig_frag,
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        rel_path = os.path.relpath(output_path, kdir)
        cc = kwargs['cc']
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
""".format(kdir=kdir, arch=kwargs['arch'], cc_env=cc_env,
           cross=kwargs['cross_compile'], output=rel_path,
           cross_compat=kwargs['cross_compile_compat'],
           llvm_ias=defconfig_opts.get('LLVM_IAS', ''),
           base=os.path.join(rel_path, '.config'),
           frag=os.path.join(rel_path, kconfig_frag_name),
           redir='> /dev/null' if not verbose else '')
        print_flush(cmd.strip())
        if log_file:
            cmd = _output_to_file(cmd, log_file, kdir)
        result = shell_cmd(cmd, True)

    tmpfile.close()
    os.unlink(tmpfile_path)

    return result


def _kernel_config_enabled(dot_config, name):
    return shell_cmd('grep -cq CONFIG_{}=y {}'.format(name, dot_config), True)


def build_kernel(build_env, kdir, arch, defconfig=None, jopt=None,
                 verbose=False, output_path=None, mod_path=None):
    """Build a linux kernel

    *build_env* is a BuildEnvironment object
    *kdir* is the path to the kernel source directory
    *defconfig* is the name of the kernel defconfig
    *jopt* is the -j option to pass to make for parallel builds
    *verbose* is whether to print all the output of the make commands
    *output_path* is the path to the directory where the binaries are made
    *mod_path* is the path to where the modules are installed

    The returned value is True if the build was successful or False if there
    was any build error.
    """
    cc = build_env.cc
    cross_compile = build_env.get_cross_compile(arch) or ''
    cross_compile_compat = build_env.get_cross_compile_compat(arch) or ''
    use_ccache = shell_cmd("which ccache > /dev/null", True)
    if jopt is None:
        jopt = int(shell_cmd("nproc")) + 2
    if not output_path:
        output_path = os.path.join(kdir, 'build')
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    if not mod_path:
        mod_path = os.path.join(output_path, '_modules_')
    build_log = 'build.log'
    log_file = os.path.join(output_path, build_log)
    dot_config = os.path.join(output_path, '.config')
    if os.path.exists(log_file):
        os.unlink(log_file)

    opts = {
        'KBUILD_BUILD_USER': 'KernelCI',
    }

    opts.update(build_env.get_arch_opts(arch))

    kwargs = {
        'kdir': kdir,
        'arch': arch,
        'cc': cc,
        'cross_compile': cross_compile,
        'cross_compile_compat': cross_compile_compat,
        'use_ccache': use_ccache,
        'output': output_path,
        'silent': not verbose,
        'log_file': log_file,
        'opts': opts,
    }

    start_time = time.time()
    defconfig_extras = []
    if defconfig:
        result = _make_defconfig(
            defconfig, kwargs, defconfig_extras, verbose, log_file)
    elif os.path.exists(dot_config):
        print_flush("Re-using {}".format(dot_config))
        result = True
    else:
        print_flush("ERROR: Missing kernel config")
        result = False
    if result:
        if _kernel_config_enabled(dot_config, 'XIP_KERNEL'):
            target = 'xipImage'
        elif _kernel_config_enabled(dot_config, 'SYS_SUPPORTS_ZBOOT'):
            target = 'vmlinuz'
        else:
            target = MAKE_TARGETS.get(arch)
        result = _run_make(jopt=jopt, target=target, **kwargs)
    mods = _kernel_config_enabled(dot_config, 'MODULES')
    if result and mods:
        result = _run_make(jopt=jopt, target='modules', **kwargs)
    if result and _kernel_config_enabled(dot_config, 'OF_FLATTREE'):
        dts_tree = os.path.join(kdir, 'arch/{}/boot/dts'.format(arch))
        if os.path.exists(dts_tree):
            result = _run_make(target='dtbs', **kwargs)
    build_time = time.time() - start_time

    if result and mods:
        if os.path.exists(mod_path):
            shutil.rmtree(mod_path)
        os.makedirs(mod_path)
        opts.update({
            'INSTALL_MOD_PATH': os.path.abspath(mod_path),
            'INSTALL_MOD_STRIP': '1',
            'STRIP': "{}strip".format(cross_compile),
        })
        result = _run_make(target='modules_install', **kwargs)

    # kselftest
    if result and "kselftest" in defconfig_extras:
        kselftest_install_path = os.path.join(output_path, '_kselftest_')
        if os.path.exists(kselftest_install_path):
            shutil.rmtree(kselftest_install_path)
        opts.update({
            'INSTALL_PATH': kselftest_install_path,
        })
        #
        # Ideally this should just be a 'make kselftest-install', but
        # due to bugs with O= in kselftest Makefile, this has to be
        # 'make -C tools/testing/selftests install'
        #
        kwargs.update({
            'kdir': os.path.join(kdir, 'tools/testing/selftests')
        })
        opts.update({
            'FORMAT': '.xz',
        })
        # 'gen_tar' target does 'make install' and creates tarball
        result = _run_make(target='gen_tar', **kwargs)

    cc_version_cmd = "{}{} --version 2>&1".format(
        cross_compile if cross_compile and cc == 'gcc' else '', cc)
    cc_version_full = shell_cmd(cc_version_cmd).splitlines()[0]

    bmeta = {
        'build_threads': jopt,
        'build_time': round(build_time, 2),
        'status': 'PASS' if result is True else 'FAIL',
        'arch': arch,
        'cross_compile': cross_compile,
        'compiler': cc,
        'compiler_version': build_env.cc_version,
        'compiler_version_full': cc_version_full,
        'build_environment': build_env.name,
        'build_log': build_log,
        'build_platform': platform.uname(),
    }

    if defconfig:
        defconfig_target = defconfig.split('+')[0]
        bmeta.update({
            'defconfig': defconfig_target,
            'defconfig_full': '+'.join([defconfig_target] + defconfig_extras),
        })
    else:
        bmeta.update({
            'defconfig': 'none',
            'defconfig_full': 'none',
        })

    vmlinux_file = os.path.join(output_path, 'vmlinux')
    if os.path.isfile(vmlinux_file):
        vmlinux_meta = kernelci.elf.read(vmlinux_file)
        bmeta.update(vmlinux_meta)
        bmeta['vmlinux_file_size'] = os.stat(vmlinux_file).st_size

    with open(os.path.join(output_path, 'bmeta.json'), 'w') as json_file:
        json.dump(bmeta, json_file, indent=4, sort_keys=True)

    return result


def install_kernel(kdir, tree_name, tree_url, git_branch, git_commit=None,
                   describe=None, describe_v=None, output_path=None,
                   publish_path=None, install_path=None, mod_path=None):
    """Install the kernel binaries in a directory for a given built revision

    Installing the kernel binaries into a new directory consists of creating a
    "bmeta.json" file with all the meta-data for the kernel build, copying the
    System.map file, the kernel .config, the build log, the frag.config file,
    all the dtbs and a tarball with all the modules.  This is an intermediate
    step between building a kernel and publishing it via the KernelCI backend.

    *kdir* is the path to the kernel source directory
    *tree_name* is the name of the tree from a build configuration
    *git_branch* is the name of the git branch in the tree
    *git_commit* is the git commit SHA
    *describe* is the "git describe" for the commit
    *describe_v* is the verbose "git describe" for the commit
    *output_path" is the path to the directory where the kernel was built
    *install_path* is the path where to install the kernel
    *mod_path* is the path where the modules were installed

    The returned value is True if it was done successfully or False if an error
    occurred.
    """
    if not install_path:
        install_path = os.path.join(kdir, '_install_')
    if not output_path:
        output_path = os.path.join(kdir, 'build')
    if not mod_path:
        mod_path = os.path.join(output_path, '_modules_')
    if not git_commit:
        git_commit = head_commit(kdir)
    if not describe:
        describe = git_describe(tree_name, kdir)
    if not describe_v:
        describe_v = git_describe_verbose(kdir)

    if os.path.exists(install_path):
        shutil.rmtree(install_path)
    os.makedirs(install_path)

    with open(os.path.join(output_path, 'bmeta.json')) as json_file:
        bmeta = json.load(json_file)

    system_map = os.path.join(output_path, 'System.map')
    if os.path.exists(system_map):
        virt_text = shell_cmd('grep " _text" {}'.format(system_map)).split()[0]
        text_offset = int(virt_text, 16) & (1 << 30)-1  # phys: cap at 1G
        shutil.copy(system_map, install_path)
    else:
        text_offset = None

    dot_config = os.path.join(output_path, '.config')
    dot_config_installed = os.path.join(install_path, 'kernel.config')
    shutil.copy(dot_config, dot_config_installed)

    build_log = os.path.join(output_path, 'build.log')
    shutil.copy(build_log, install_path)

    frags = os.path.join(output_path, 'frag.config')
    if os.path.exists(frags):
        shutil.copy(frags, install_path)

    arch = bmeta['arch']
    boot_dir = os.path.join(output_path, 'arch', arch, 'boot')
    kimage_names = KERNEL_IMAGE_NAMES[arch]
    kimages = []
    kimage_file = None
    for root, _, files in os.walk(boot_dir):
        for name in kimage_names:
            if name in files:
                kimages.append(name)
                image_path = os.path.join(root, name)
                shutil.copy(image_path, install_path)
    for files in os.listdir(output_path):
        for name in kimage_names:
            if name == files:
                kimages.append(name)
                image_path = os.path.join(output_path, name)
                shutil.copy(image_path, install_path)
    if kimages:
        for name in kimage_names:
            if name in kimages:
                kimage_file = name
                break
    if not kimage_file:
        print_flush("Warning: no kernel image found")

    dts_dir = os.path.join(boot_dir, 'dts')
    dtbs = os.path.join(install_path, 'dtbs')
    dtb_list = []
    for root, _, files in os.walk(dts_dir):
        for f in fnmatch.filter(files, '*.dtb'):
            dtb_path = os.path.join(root, f)
            dtb_rel = os.path.relpath(dtb_path, dts_dir)
            dtb_list.append(dtb_rel)
            dest_path = os.path.join(dtbs, dtb_rel)
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy(dtb_path, dest_path)
    with open(os.path.join(install_path, 'dtbs.json'), 'w') as json_file:
        json.dump({'dtbs': sorted(dtb_list)}, json_file, indent=4)

    modules_tarball = None
    if os.path.exists(mod_path):
        modules_tarball = 'modules.tar.xz'
        modules_tarball_path = os.path.join(install_path, modules_tarball)
        shell_cmd("tar -C{path} -cJf {tarball} .".format(
            path=mod_path, tarball=modules_tarball_path))

    # 'make gen_tar' creates this tarball path
    kselftest_tarball = 'kselftest-packages/kselftest.tar.xz'
    kselftest_tarball_path = os.path.join(output_path, '_kselftest_',
                                          kselftest_tarball)
    if os.path.exists(kselftest_tarball_path):
        kselftest_tarball = os.path.basename(kselftest_tarball_path)
        shutil.copy(kselftest_tarball_path,
                    os.path.join(install_path, kselftest_tarball))
    else:
        kselftest_tarball = kselftest_tarball_path = None

    build_env = bmeta['build_environment']
    defconfig_full = bmeta['defconfig_full']
    if not publish_path:
        publish_path = '/'.join(item.replace('/', '-') for item in [
            tree_name, git_branch, describe, arch, defconfig_full, build_env,
        ])

    bmeta.update({
        'kconfig_fragments': 'frag.config' if os.path.exists(frags) else '',
        'kernel_image': kimage_file,
        'kernel_config': os.path.basename(dot_config_installed),
        'system_map': 'System.map' if os.path.exists(system_map) else None,
        'text_offset': '0x{:08x}'.format(text_offset) if text_offset else None,
        'dtb_dir': 'dtbs' if os.path.exists(dtbs) else None,
        'modules': modules_tarball,
        'job': tree_name,
        'git_url': tree_url,
        'git_branch': git_branch,
        'git_describe': describe,
        'git_describe_v': describe_v,
        'git_commit': git_commit,
        'file_server_resource': publish_path,
        'kselftests': kselftest_tarball,
    })

    with open(os.path.join(install_path, 'bmeta.json'), 'w') as json_file:
        json.dump(bmeta, json_file, indent=4, sort_keys=True)

    return True


def push_kernel(kdir, api, token, install_path=None):
    """Push the kernel binaries to the storage server

    Push the kernel image, the modules tarball, the dtbs and the build.json
    meta-data to the storage server via the KernelCI backend API.

    *kdir* is the path to the kernel source directory
    *api* is the URL of the KernelCI backend API
    *token* is the token to use with the KernelCI backend API
    *install_path* is the path to the installation directory

    The returned value is True if it was done successfully or False if an error
    occurred.
    """
    if not install_path:
        install_path = os.path.join(kdir, '_install_')

    with open(os.path.join(install_path, 'bmeta.json')) as f:
        bmeta = json.load(f)

    artifacts = {}
    for root, _, files in os.walk(install_path):
        for f in files:
            px = os.path.relpath(root, install_path)
            artifacts[os.path.join(px, f)] = open(os.path.join(root, f), "rb")
    upload_path = bmeta['file_server_resource']
    print_flush("Upload path: {}".format(upload_path))
    upload_files(api, token, upload_path, artifacts)

    return True


def publish_kernel(kdir, install_path=None, api=None, token=None,
                   json_path=None):
    """Publish a kernel via the KernelCI backend API or in a JSON file

    If api and token are provided, the the kernel is published via the KernelCI
    backend API.  If json_path is provided, the same data is written to a JSON
    file locally.  This is especially useful for bisections which push kernel
    binaries but don't publish kernels via the backend.  The JSON file can be
    used later on to generate matching test jobs rather than querying the
    backend API again.

    *kdir* is the path to the kernel source directory
    *install_path* is the directory where the binaries were installed
    *api* is the URL of the KernelCI backend API
    *token* is the token to use with the KernelCI backend API
    *json_path* is the path to a JSON file where to store the publish data

    The returned value is True if it was done successfully or False if an error
    occurred.
    """

    if not install_path:
        install_path = os.path.join(kdir, '_install_')

    with open(os.path.join(install_path, 'bmeta.json')) as f:
        bmeta = json.load(f)

    if json_path:
        with open(os.path.join(install_path, 'dtbs.json')) as f:
            dtbs = json.load(f)['dtbs']
        bmeta['dtb_dir_data'] = dtbs
        try:
            with open(json_path, 'r') as json_file:
                full_json = json.load(json_file)
            full_json.append(bmeta)
        except Exception as e:
            full_json = [bmeta]
        with open(json_path, 'w') as json_file:
            json.dump(full_json, json_file)

    if api and token:
        data = {k: bmeta[v] for k, v in {
            'path': 'file_server_resource',
            'file_server_resource': 'file_server_resource',
            'job': 'job',
            'git_branch': 'git_branch',
            'arch': 'arch',
            'kernel': 'git_describe',
            'build_environment': 'build_environment',
            'defconfig': 'defconfig',
            'defconfig_full': 'defconfig_full',
        }.items()}
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
        }
        url = urllib.parse.urljoin(api, '/build')
        data_json = json.dumps(data)
        resp = requests.post(url, headers=headers, data=data_json)
        resp.raise_for_status()

    return True


def load_json(bmeta_json, dtbs_json=None):
    """Load the build meta-data from JSON files and return dictionaries

    *bmeta_json* is the path to a kernel build meta-data JSON file
    *dtbs_json* is the path to an optional kernel dtbs JSON file

    The returned value is a 2-tuple with the bmeta and dtbs data.
    """
    with open(bmeta_json) as json_file:
        bmeta = json.load(json_file)
    if dtbs_json:
        with open(dtbs_json) as json_file:
            dtbs = json.load(json_file)['dtbs']
    else:
        dtbs = {'dtbs': []}
    return bmeta, dtbs
