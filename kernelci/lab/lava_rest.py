# Copyright (C) 2021 Collabora Limited
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

import requests
import urllib.parse

from .lava import LAVA


class LAVAREST(LAVA):

    def connect(self, user=None, token=None):
        super().connect(user, token)
        self._lava_token = token

    def _rest_query(self, endpoint, ordering, limit=50):
        base_url = urllib.parse.urljoin(
            self.config.url, f'api/v0.2/{endpoint}/'
        )
        headers = {'Authorization': f"Token {self._lava_token}"}
        offset = 0
        results = []
        while True:
            query = urllib.parse.urlencode(
                {'offset': offset, 'limit': limit, 'ordering': ordering}
            )
            url = '?'.join([base_url, query])
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data['results'])
            total = int(data['count'])
            if len(results) < total:
                offset += limit
            else:
                break
        return results

    def _get_devices(self):
        devices = self._rest_query('devices', 'hostname')
        all_devices = [
            tuple(dev[key] for key in ['hostname', 'device_type', 'health'])
            for dev in devices
        ]

        aliases = self._rest_query('aliases', 'name')
        all_aliases = {
            alias['name']: alias['device_type']
            for alias in aliases
        }

        device_types = {}
        for device in all_devices:
            name, device_type, health = device
            device_list = device_types.setdefault(device_type, list())
            device_list.append({
                'name': name,
                'online': health == "Good",
            })
        online_status = {
            device_type: any(device['online'] for device in devices)
            for device_type, devices in device_types.items()
        }

        return {
            'online_status': online_status,
            'aliases': all_aliases,
        }


def get_api(lab):
    """Get a LAVA lab API object"""
    return LAVAREST(lab)
