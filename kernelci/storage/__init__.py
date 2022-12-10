# Copyright (C) 2020, 2021, 2022 Collabora Limited
# Author: Lakshmipathi Ganapathi <lakshmipathi.ganapathi@collabora.com>
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

import importlib
import os
import requests
from urllib.parse import urljoin
from kernelci import shell_cmd


def discover_files(path):
    """Discover files recustively so they can then be uploaded

    Recursively walk through a file hierarchy and return a dictionary with the
    file paths and open file objects which can then be passed directly to
    upload_files().

    *path* is the path to the file hierarchy where to look for files
    """
    artifacts = {}
    for root, _, files in os.walk(path):
        for fname in files:
            px = os.path.relpath(root, path)
            artifacts[os.path.join(px, fname)] = open(
                os.path.join(root, fname), "rb")
    return artifacts


def upload_files(api, token, path, input_files):
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


class Storage:
    """Storage abstraction interface class"""

    def __init__(self, config, credentials):
        """Base class for interacting with a storage implementation

        *config* is the storage configuration object loaded from YAML
        *credentials* is an arbitrary object with credentials for the storage
        """
        self._config = config
        self._credentials = credentials

    @property
    def config(self):
        return self._config

    @property
    def credentials(self):
        return self._credentials

    def _upload(self, file_path, dest_path):
        """Implementation method to upload files"""
        raise NotImplementedError("_upload() needs to be implemented")

    def upload_single(self, file_path, dest_path=''):
        """Upload a single file to storage

        Upload the file located in *file_path* to the storage at the
        destination specified by *dest_path*.  Path elements from *file_path*
        are not included in the destination path.  The returned value is the
        full public URL that can be used to retrieve the file again.
        """
        self._upload([file_path], dest_path)
        return urljoin(
            self.config.base_url,
            '/'.join([dest_path, os.path.basename(file_path)])
        )

    def upload_multiple(self, file_paths, dest_path=''):
        """Upload multiple files to storage

        Upload all the files listed in *file_paths* to storage at the
        destination speciified by *dest_path*.  The path elements in the file
        paths are not included in the destination paths.  The returned value is
        a list with the public URL to retrieve each file matching the input
        list in *file_paths*.
        """
        self._upload(file_paths, dest_path)
        return [
            urljoin(
                self.config.base_url,
                '/'.join([dest_path, os.path.basename(file_path)])
            )
            for file_path in file_paths
        ]


def get_storage(config, credentials):
    """Get a Storage instance for a given storage configuration

    Create and return a Storage implementation object instance that matches the
    storage configuration in *config* using the provided *credentials*.
    """
    m = importlib.import_module('.'.join([
        'kernelci', 'storage', config.storage_type
    ]))
    return m.get_storage(config, credentials)
