# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2020-2023 Collabora Limited
# Author: Lakshmipathi Ganapathi <lakshmipathi.ganapathi@collabora.com>
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI storage abstraction package"""

import importlib
import os
from urllib.parse import urljoin


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
        """Configuration object loaded from YAML"""
        return self._config

    @property
    def credentials(self):
        """Credentials data"""
        return self._credentials

    def _upload(self, file_paths, dest_path):
        """Implementation method to upload files

        The *file_paths* and *dest_path* arguments are of the same form as
        passed to .upload_multiple().
        """
        raise NotImplementedError("_upload() needs to be implemented")

    def upload_single(self, file_path, dest_path=''):
        """Upload a single file to storage

        Upload the file specified by the *file_path* 2-tuple as (local, remote)
        file names to the storage at the destination directory specified by
        *dest_path*.  Any path elements in the 2nd item of *file_path* will be
        used as part as the full destination path.  The returned value is the
        full public URL that can be used to retrieve the file again.

        For example:

            s.upload_single(('path/to/local-file.txt', 'file.txt'), '.')
        """
        self._upload([file_path], dest_path)
        return urljoin(
            self.config.base_url,
            '/'.join([dest_path, file_path[1]])
        )

    def upload_multiple(self, file_paths, dest_path=''):
        """Upload multiple files to storage

        Upload all the files *file_paths* as a list of 2-tuples with (local,
        remote) file names to storage at the destination directory specified by
        *dest_path*.  Any path elements in the remove file paths will be
        included in the final destination paths.  The returned value is a list
        with the public URL to retrieve each file matching the input list in
        *file_paths*.

        For example:

            s.upload_multiple(
                [
                    ('path/to/local-file.txt', 'file.txt'),
                    ('path/to/other-file.txt', 'subdir/other.txt'),
                ],
                'data/path'
            )
        """
        self._upload(file_paths, dest_path)
        return [
            urljoin(self.config.base_url, '/'.join([dest_path, file_dst]))
            for (file_src, file_dst) in file_paths
        ]


def get_storage(config, credentials):
    """Get a Storage instance for a given storage configuration

    Create and return a Storage implementation object instance that matches the
    storage configuration in *config* using the provided *credentials*.
    """
    module = importlib.import_module('.'.join([
        'kernelci', 'storage', config.storage_type
    ]))
    return module.get_storage(config, credentials)
