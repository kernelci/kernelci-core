# Copyright (C) 2018, 2019 Collabora Limited
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

import fnmatch
import json
import os
import platform
import requests
import shutil
import stat
import subprocess
import tempfile
import time
import urlparse

from kernelci import shell_cmd
import kernelci.configs
import kernelci.elf

# This is used to get the mainline tags as a minimum for git describe
TORVALDS_GIT_URL = \
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"

# Hard-coded make targets for each CPU architecture
MAKE_TARGETS = {
    'arm': 'zImage',
    'arm64': 'Image',
    'arc': 'uImage.gz',
}

# Hard-coded binary kernel image names for each CPU architecture
KERNEL_IMAGE_NAMES = {
    'arm': ['zImage', 'xipImage'],
    'arm64': ['Image'],
    'arc': ['uImage.gz'],
    'i386': ['bzImage'],
    'mips': ['uImage.gz', 'vmlinux.gz.itb'],
    'riscv': ['Image', 'Image.gz'],
    'x86_64': ['bzImage'],
    'x86': ['bzImage'],
}


def _get_last_commit_file_name(config):
    return '_'.join(['last-commit', config.name])


def _upload_files(api, token, path, input_files):
    headers = {
        'Authorization': token,
    }
    data = {
        'path': path,
    }
    files = {
        'file{}'.format(i): (name, fobj)
        for i, (name, fobj) in enumerate(input_files.iteritems())
    }
    url = urlparse.urljoin(api, 'upload')
    resp = requests.post(url, headers=headers, data=data, files=files)
    resp.raise_for_status()


def get_last_commit(config, storage):
    last_commit_url = "{storage}/{tree}/{file_name}".format(
        storage=storage, tree=config.tree.name,
        file_name=_get_last_commit_file_name(config))
    last_commit_resp = requests.get(last_commit_url)
    if last_commit_resp.status_code != 200:
        return False
    return last_commit_resp.text.strip()


def update_last_commit(config, api, token, commit):
    _upload_files(api, token, config.tree.name,
                  {_get_last_commit_file_name(config): commit})


def get_branch_head(config):
    cmd = "git ls-remote {url} refs/heads/{branch}".format(
        url=config.tree.url, branch=config.branch)
    head = shell_cmd(cmd)
    if not head:
        return False
    return head.split()[0]


def check_new_commit(config, storage):
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
cd {path}
git fetch --tags {url}
""".format(path=path, url=url))


def update_mirror(config, path):
    if not os.path.exists(path):
        shell_cmd("""
mkdir -p {path}
cd {path}
git init --bare
""".format(path=path))

    _update_remote(config, path)


def update_repo(config, path, ref):
    if not os.path.exists(path):
        shell_cmd("""
git clone --reference={ref} -o {remote} {url} {path}
""".format(ref=ref, remote=config.tree.name, url=config.tree.url, path=path))

    _update_remote(config, path)
    _fetch_tags(path)

    shell_cmd("""
cd {path}
git reset --hard
git clean -fd
git fetch --tags {remote}
git checkout --detach {remote}/{branch}
""".format(path=path, remote=config.tree.name, branch=config.branch))


def head_commit(path):
    cmd = """\
cd {path} &&
git log --pretty=format:%H -n1
""".format(path=path)
    commit = shell_cmd(cmd)
    return commit.strip()


def git_describe(tree_name, path):
    describe_args = "--match=v\*" if tree_name == "arm-soc" else ""
    cmd = """\
cd {path} && \
git describe {describe_args} \
""".format(path=path, describe_args=describe_args)
    describe = shell_cmd(cmd)
    return describe.strip().replace('/', '_')


def git_describe_verbose(path):
    cmd = """\
cd {path} &&
git describe --match=v[1-9]\* \
""".format(path=path)
    describe = shell_cmd(cmd)
    return describe.strip()


def add_kselftest_fragment(path, frag_path='kernel/configs/kselftest.config'):
    shell_cmd("""
cd {path} &&
find tools/testing/selftests -name config -printf "#\n# %h/%f\n#\n" -exec cat {{}} \; > {frag_path}
""".format(path=path, frag_path=frag_path))


def make_tarball(path, tarball_name):
    cmd = "tar -czf {name} --exclude=.git -C {path} .".format(
        path=path, name=tarball_name)
    subprocess.check_output(cmd, shell=True)


def generate_config_fragment(frag, kdir):
    with open(os.path.join(kdir, frag.path), 'w') as f:
        print(frag.path)
        for kernel_config in frag.configs:
            f.write(kernel_config + '\n')


def generate_fragments(config, kdir):
    for variant in config.variants:
        for frag in variant.fragments:
            if frag.name == 'kselftest':
                print(frag.path)
                add_kselftest_fragment(kdir)
            elif frag.configs:
                generate_config_fragment(frag, kdir)


def push_tarball(config, kdir, storage, api, token):
    tarball_name = "linux-src_{}.tar.gz".format(config.name)
    describe = git_describe(config.tree.name, kdir)
    tarball_url = '/'.join([
        storage, config.tree.name, config.branch, describe, tarball_name])
    resp = requests.head(tarball_url)
    if resp.status_code == 200:
        return tarball_url
    tarball = "{}.tar.gz".format(config.name)
    make_tarball(kdir, tarball)
    path = '/'.join([config.tree.name, config.branch, describe]),
    _upload_files(api, token, path, {tarball_name: open(tarball)})
    os.unlink(tarball)
    return tarball_url


def _add_frag_configs(kdir, frag_list, frag_paths, frag_configs):
    for frag in frag_list:
        if os.path.exists(os.path.join(kdir, frag.path)):
            if frag.defconfig:
                frag_configs.add(frag.defconfig)
            else:
                frag_paths.add(frag.path)


def list_kernel_configs(config, kdir, single_variant=None, single_arch=None):
    kernel_configs = set()

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
                if arch.match({'defconfig': defconfig}):
                    kernel_configs.add((arch.name, defconfig, build_env))

    return kernel_configs


def _run_make(kdir, arch, target=None, jopt=None, silent=True, cc='gcc',
              cross_compile=None, use_ccache=None, output=None, log_file=None,
              opts=None):
    args = ['make']

    if opts:
        args += ['='.join([k, v]) for k, v in opts.iteritems()]

    args += ['-C{}'.format(kdir)]

    if jopt:
        args.append('-j{}'.format(jopt))

    if silent:
        args.append('-s')

    args.append('ARCH={}'.format(arch))

    if cross_compile:
        args.append('CROSS_COMPILE={}'.format(cross_compile))

    args.append('HOSTCC={}'.format(cc))

    if use_ccache:
        px = cross_compile if cc == 'gcc' and cross_compile else ''
        args.append('CC="ccache {}{}"'.format(px, cc))
        os.environ.setdefault('CCACHE_DIR',
                              os.path.join(kdir, '-'.join(['.ccache', arch])))
    elif cc != 'gcc':
        args.append('CC={}'.format(cc))

    if output:
        args.append('O={}'.format(os.path.relpath(output, kdir)))

    if target:
        args.append(target)

    cmd = ' '.join(args)
    print(cmd)
    if log_file:
        open(log_file, 'a').write("#\n# {}\n#\n".format(cmd))
        cmd = "/bin/bash -c '(set -o pipefail; {} 2>&1 | tee -a {})'".format(
            cmd, log_file)
    return shell_cmd(cmd, True)


def _make_defconfig(defconfig, kwargs, fragments):
    kdir, output_path = (kwargs.get(k) for k in ('kdir', 'output'))
    result = True

    tmpfile_fd, tmpfile_path = tempfile.mkstemp(prefix='kconfig-')
    tmpfile = os.fdopen(tmpfile_fd, 'w')
    defs = defconfig.split('+')
    target = defs.pop(0)
    for d in defs:
        if d.startswith('CONFIG_'):
            tmpfile.write(d + '\n')
            fragments.append(d)
        else:
            frag_path = os.path.join(kdir, d)
            if os.path.exists(frag_path):
                with open(frag_path) as frag:
                    tmpfile.write("\n# fragment from : {}\n".format(d))
                    tmpfile.writelines(frag)
                fragments.append(os.path.basename(os.path.splitext(d)[0]))
    tmpfile.flush()
    if not _run_make(target=target, **kwargs):
        result = False

    if result and fragments:
        kconfig_frag_name = 'frag.config'
        kconfig_frag = os.path.join(output_path, kconfig_frag_name)
        shutil.copy(tmpfile_path, kconfig_frag)
        os.chmod(kconfig_frag,
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        rel_path = os.path.relpath(output_path, kdir)
        cmd = """\
cd {kdir}
export ARCH={arch}
scripts/kconfig/merge_config.sh -O {output} '{base}' '{frag}' > /dev/null 2>&1
""".format(kdir=kdir, arch=kwargs['arch'],output=rel_path,
           base=os.path.join(rel_path, '.config'),
           frag=os.path.join(rel_path, kconfig_frag_name))
        print(cmd.strip())
        result = shell_cmd(cmd, True)

    tmpfile.close()
    os.unlink(tmpfile_path)

    return result


def _kernel_config_enabled(dot_config, name):
    return shell_cmd('grep -cq CONFIG_{}=y {}'.format(name, dot_config), True)


def build_kernel(build_env, kdir, arch, defconfig=None, jopt=None,
                 verbose=False, output_path=None, mod_path='_modules_'):
    cc = build_env.cc
    cross_compile = build_env.get_cross_compile(arch) or None
    use_ccache = shell_cmd("which ccache > /dev/null", True)
    if jopt is None:
        jopt = int(shell_cmd("nproc")) + 2
    if not output_path:
        output_path = os.path.join(kdir, 'build')
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    build_log = 'build.log'
    log_file = os.path.join(output_path, build_log)
    dot_config = os.path.join(output_path, '.config')
    if os.path.exists(log_file):
        os.unlink(log_file)

    opts = {
        'KBUILD_BUILD_USER': 'KernelCI',
    }

    kwargs = {
        'kdir': kdir,
        'arch': arch,
        'cc': cc,
        'cross_compile': cross_compile,
        'use_ccache': use_ccache,
        'output': output_path,
        'silent': not verbose,
        'log_file': log_file,
        'opts': opts,
    }

    start_time = time.time()
    fragments = []
    if defconfig:
        result = _make_defconfig(defconfig, kwargs, fragments)
    elif os.path.exists(dot_config):
        print("Re-using {}".format(dot_config))
        result = True
    else:
        print("ERROR: Missing kernel config")
        result = False
    if result:
        target = (
            'xipImage' if _kernel_config_enabled(dot_config, 'XIP_KERNEL')
            else MAKE_TARGETS.get(arch)
        )
        result = _run_make(jopt=jopt, target=target, **kwargs)
    mods = _kernel_config_enabled(dot_config, 'MODULES')
    if result and mods:
        result = _run_make(jopt=jopt, target='modules', **kwargs)
    if result and _kernel_config_enabled(dot_config, 'OF_FLATTREE'):
        dts_tree = os.path.join(kdir, 'arch/{}/boot/dts'.format(arch))
        if os.path.exists(dts_tree):
            result = _run_make(target='dtbs', **kwargs)
    build_time = time.time() - start_time

    if result and mods and mod_path:
        abs_mod_path = os.path.join(output_path, mod_path)
        if os.path.exists(abs_mod_path):
            shutil.rmtree(abs_mod_path)
        os.makedirs(abs_mod_path)
        opts.update({
            'INSTALL_MOD_PATH': mod_path,
            'INSTALL_MOD_STRIP': '1',
            'STRIP': "{}strip".format(cross_compile or ''),
        })
        result = _run_make(target='modules_install', **kwargs)

    cc_version_cmd = "{}{} --version 2>&1".format(
        cross_compile if cross_compile and cc == 'gcc' else '', cc)
    cc_version_full = shell_cmd(cc_version_cmd).splitlines()[0]

    bmeta = {
        'build_threads': jopt,
        'build_time': round(build_time, 2),
        'build_result': 'PASS' if result is True else 'FAIL',
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
            'defconfig_full': '+'.join([defconfig_target] + fragments),
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
                   install='_install_', mod_path='_modules_'):
    install_path = os.path.join(kdir, install)
    if not output_path:
        output_path = os.path.join(kdir, 'build')
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
    if kimages:
        for name in kimage_names:
            if name in kimages:
                kimage_file = name
                break
    if not kimage_file:
        print("Warning: no kernel image found")

    dts_dir = os.path.join(boot_dir, 'dts')
    dtbs = os.path.join(install_path, 'dtbs')
    for root, _, files in os.walk(dts_dir):
        for f in fnmatch.filter(files, '*.dtb'):
            dtb_path = os.path.join(root, f)
            dtb_rel = os.path.relpath(dtb_path, dts_dir)
            dest_path = os.path.join(dtbs, dtb_rel)
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy(dtb_path, dest_path)

    modules_tarball = None
    if mod_path:
        abs_mod_path = os.path.join(output_path, mod_path)
        if os.path.exists(abs_mod_path):
            modules_tarball = 'modules.tar.xz'
            modules_tarball_path = os.path.join(install_path, modules_tarball)
            shell_cmd("tar -C{path} -cJf {tarball} .".format(
                path=abs_mod_path, tarball=modules_tarball_path))

    build_env = bmeta['build_environment']
    defconfig_full = bmeta['defconfig_full']
    publish_path = '/'.join([
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
        'git_describe_verbose': describe_v,
        'git_commit': git_commit,
        'file_server_resource': publish_path,
    })

    with open(os.path.join(install_path, 'build.json'), 'w') as json_file:
        json.dump(bmeta, json_file, indent=4, sort_keys=True)

    return True


def push_kernel(kdir, api, token, install='_install_'):
    install_path = os.path.join(kdir, install)

    with open(os.path.join(install_path, 'build.json')) as f:
        bmeta = json.load(f)

    artifacts = {}
    for root, _, files in os.walk(install_path):
        for f in files:
            px = os.path.relpath(root, install_path)
            artifacts[os.path.join(px, f)] = open(os.path.join(root, f))
    upload_path = bmeta['file_server_resource']
    print("Upload path: {}".format(upload_path))
    _upload_files(api, token, upload_path, artifacts)

    return True


def publish_kernel(kdir, install='_install_', api=None, token=None,
                   json_path=None):
    install_path = os.path.join(kdir, install)

    with open(os.path.join(install_path, 'build.json')) as f:
        bmeta = json.load(f)

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
    }.iteritems()}

    if json_path:
        json_data = dict(data)
        for k in ['kernel_image', 'modules', 'git_commit', 'git_url']:
            json_data[k] = bmeta[k]
        json_data['status'] = bmeta['build_result']
        dtb_data = []
        if bmeta['dtb_dir']:
            dtb_dir = os.path.join(install_path, bmeta['dtb_dir'])
            for root, dirs, files in os.walk(dtb_dir):
                if root != dtb_dir:
                    rel = os.path.relpath(root, dtb_dir)
                    files = list(os.path.join(rel, dtb) for dtb in files)
                dtb_data += files
        json_data['dtb_dir_data'] = dtb_data
        try:
            with open(json_path, 'r') as json_file:
                full_json = json.load(json_file)
            full_json.append(json_data)
        except Exception as e:
            full_json = [json_data]
        with open(json_path, 'w') as json_file:
            json.dump(full_json, json_file)

    if api and token:
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
        }

        url = urlparse.urljoin(api, '/build')
        json_data = json.dumps(data)
        resp = requests.post(url, headers=headers, data=json_data)
        resp.raise_for_status()

    return True
