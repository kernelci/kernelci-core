# Copyright (C) 2020 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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


def _submit_backend(name, config, data, token):
    if token is None:
        print('API token must be provided')
        return False
    resp = requests.post(config.url,
                         json=json.loads(data),
                         headers={'Authorization': token})
    print("Status: {}".format(resp.status_code))
    print(resp.text)
    return 200 <= resp.status_code <= 300


def submit(name, config, data, token=None):
    if config.db_type == "kernelci_backend":
        return _submit_backend(name, config, data, token)
    else:
        raise ValueError("db_type not supported: {}".format(config.db_type))
