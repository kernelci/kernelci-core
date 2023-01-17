# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

# Needed to use open() in dictionary comprehension
# pylint: disable=consider-using-with

"""KernelCI storage implementation for kernelci-backend"""

from urllib.parse import urljoin
import requests
from . import Storage


class StorageBackend(Storage):
    """Storage implementation for kernelci-backend

    This class implements the Storage interface for the kernelci-backend API.
    It requires an API token as credentials.
    """

    def _upload(self, file_paths, dest_path):
        headers = {
            'Authorization': self.credentials,
        }
        data = {
            'path': dest_path,
        }
        files = {
            f'file{i}': (file_dst, open(file_src, 'rb'))
            for i, (file_src, file_dst) in enumerate(file_paths)
        }
        url = urljoin(self.config.api_url, 'upload')
        resp = requests.post(url, headers=headers, data=data, files=files)
        resp.raise_for_status()


def get_storage(config, credentials):
    """Get a Storage_backend object"""
    return StorageBackend(config, credentials)
