# Copyright (C) 2022 Collabora Limited
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
from . import Storage


class Storage_backend(Storage):
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
            f'file{i}': (os.path.basename(file_path), open(file_path, 'rb'))
            for i, file_path in enumerate(file_paths)
        }
        url = urljoin(self.config.api_url, 'upload')
        resp = requests.post(url, headers=headers, data=data, files=files)
        resp.raise_for_status()


def get_storage(config, credentials):
    """Get a Storage_backend object"""
    return Storage_backend(config, credentials)
