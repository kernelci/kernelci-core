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


def get_last_commit(config, storage):
    last_commit_url = "{storage}/{tree}/{branch}/last.commit".format(
        storage=storage, tree=config.tree.name, branch=config.branch)
    last_commit_resp = requests.get(last_commit_url)
    if last_commit_resp.status_code != 200:
        return False
    return last_commit_resp.text.strip()


def update_last_commit(config, api, token, commit, file_name='last.commit'):
    headers = {
        'Authorization': token,
    }
    data = {
        'path': '/'.join([config.tree.name, config.branch]),
    }
    files = {
        'file': (file_name, commit),
    }
    url = urlparse.urljoin(api, 'upload')
    resp = requests.post(url, headers=headers, data=data, files=files)
    resp.raise_for_status()


def get_branch_head(config):
    cmd = "git ls-remote {url} refs/heads/{branch}".format(
        url=config.tree.url, branch=config.branch)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    head, _ = p.communicate()
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

    shell_cmd("""
cd {path}
git reset --hard
git clean -fd
git fetch --tags {remote}
git checkout --detach {remote}/{branch}
""".format(path=path, remote=config.tree.name, branch=config.branch))


def head_commit(config, path):
    cmd = """\
cd {path} &&
git log --pretty=format:%H -n1
""".format(path=path)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    commit, _ = p.communicate()
    return commit.strip()


def git_describe(config, path):
    describe_args = "--match=v\*" if config.tree.name == "arm-soc" else ""
    cmd = """\
cd {path} && \
git describe {describe_args} \
""".format(path=path, describe_args=describe_args)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    describe, _ = p.communicate()
    return describe.strip().replace('/', '_')


def git_describe_verbose(config, path):
    cmd = """\
cd {path} &&
git describe --match=v[1-9]\* \
""".format(path=path)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    describe, _ = p.communicate()
    return describe.strip()


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


def push_tarball(config, path, storage, api, token,
                 tarball_name='linux-src.tar.gz'):
    describe = git_describe(config, path)
    tarball_url = '/'.join([
        storage, config.tree.name, config.branch, describe, tarball_name])
    resp = requests.head(tarball_url)
    if resp.status_code == 200:
        return tarball_url
    tarball = "{}.tar.gz".format(config.name)
    make_tarball(path, tarball)
    upload_tarball(config, path, api, token, tarball, tarball_name, describe)
    os.unlink(tarball)
    return tarball_url
