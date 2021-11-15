# Copyright (C) 2020, 2021 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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

import json
import requests
import urllib
from kernelci.data import Database


class KernelCIBackend(Database):

    def __init__(self, config, token):
        super().__init__(config, token)
        if self._token is None:
            raise ValueError("API token required for kernelci_backend")
        self._headers = {'Authorization': self._token}

    def _submit(self, path, data, verbose):
        url = urllib.parse.urljoin(self.config.url, path)
        resp = requests.post(url, json=data, headers=self._headers)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            self._print_http_error(ex, verbose)
            return False
        if verbose:
            print(resp.text)
        return True

    def submit(self, data, verbose=False):
        for path, item in data.items():
            if not self._submit(path, item, verbose):
                return False
        return True

    def submit_build(self, meta, verbose=False):
        return self._submit('build', meta.get(), verbose)

    def submit_test(self, results, verbose=False):
        return self._submit('test', results, verbose)


def get_db(config, token):
    """Get a KernelCI backend database object"""
    return KernelCIBackend(config, token)
