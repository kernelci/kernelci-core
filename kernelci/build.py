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

import os
import requests
import subprocess
import urlparse

from kernelci import shell_cmd
import kernelci.configs

# This is used to get the mainline tags as a minimum for git describe
TORVALDS_GIT_URL = \
    "git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"


def _get_last_commit_file_name(config):
    return '_'.join(['last-commit', config.name])


def get_last_commit(config, storage):
    last_commit_url = "{storage}/{tree}/{file_name}".format(
        storage=storage, tree=config.tree.name,
        file_name=_get_last_commit_file_name(config))
    last_commit_resp = requests.get(last_commit_url)
    if last_commit_resp.status_code != 200:
        return False
    return last_commit_resp.text.strip()


def update_last_commit(config, api, token, commit):
    headers = {
        'Authorization': token,
    }
    data = {
        'path': config.tree.name,
    }
    files = {
        'file': (_get_last_commit_file_name(config), commit),
    }
    url = urlparse.urljoin(api, 'upload')
    resp = requests.post(url, headers=headers, data=data, files=files)
    resp.raise_for_status()


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


def upload_tarball(config, path, api, token, tarball, file_name, describe):
    headers = {
        'Authorization': token,
    }
    data = {
        'path': '/'.join([config.tree.name, config.branch, describe]),
    }
    files = {
        'file': (file_name, open(tarball),),
    }
    url = urlparse.urljoin(api, 'upload')
    resp = requests.post(url, headers=headers, data=data, files=files)
    resp.raise_for_status()


def generate_fragments(config, kdir):
    add_kselftest_fragment(kdir)
    for variant in config.variants:
        for frag in variant.fragments:
            if frag.configs:
                with open(os.path.join(kdir, frag.path), 'w') as f:
                    print(frag.path)
                    for kernel_config in frag.configs:
                        f.write(kernel_config + '\n')


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
    upload_tarball(config, kdir, api, token, tarball, tarball_name, describe)
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
        cc = variant.build_environment.cc
        cc_version = variant.build_environment.cc_version
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
                    kernel_configs.add((arch.name, defconfig, cc, cc_version))

    return kernel_configs
