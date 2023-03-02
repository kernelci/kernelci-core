# Copyright (C) 2022-2023 Collabora Limited
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
from urllib.parse import urljoin
from kernelci.build import get_branch_head, git_describe, make_tarball


class Args:

    storage = {
        'name': '--storage',
        'help': "Storage URL",
    }


def _upload_files(api, token, path, input_files):
    """Upload rootfs to KernelCI backend.

    *api* is the URL of the KernelCI backend API
    *token* is the backend API token to use
    *path* is the target on KernelCI backend
    *input_files* dictionary of input files
    """
    headers = {
        'Authorization': token,
    }
    data = {
        'path': path,
    }
    files = {
        'file{}'.format(i): (name, fobj)
        for i, (name, fobj) in enumerate(input_files.items())
    }
    url = urljoin(api, 'upload')
    resp = requests.post(url, headers=headers, data=data, files=files)
    resp.raise_for_status()


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
    _upload_files(api, token, config.tree.name,
                  {_get_last_commit_file_name(config): commit})


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
    tarball_url = urljoin(storage, '/'.join([path, tarball_name]))
    resp = requests.head(tarball_url)
    if resp.status_code == 200:
        return tarball_url
    tarball = "{}.tar.gz".format(config.name)
    make_tarball(kdir, tarball)
    _upload_files(api, token, path, {tarball_name: open(tarball, 'rb')})
    os.unlink(tarball)
    return tarball_url
