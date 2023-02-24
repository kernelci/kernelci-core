# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>

import xmlrpc.client
import urllib.parse

from . import LavaRuntime

DEVICE_ONLINE_STATUS = ['idle', 'running', 'reserved']


class LAVA(LavaRuntime):
    """Interface to a LAVA lab

    This implementation of kernelci.runtime.LabAPI is to communicate with LAVA
    labs.  It can retrieve some information such as the list of devices and
    their online status, generate and submit jobs with callback parameters.
    One special thing it can deal with is job priorities, which is only
    available in kernelci.config.runtime.lab_LAVA objects.
    """

    def _get_devices(self):
        all_devices = self._server.scheduler.all_devices()

        all_aliases = dict()
        for device_type_data in self._server.scheduler.device_types.list():
            name = device_type_data['name']
            aliases = self._server.scheduler.device_types.aliases.list(name)
            for alias in aliases:
                all_aliases[alias] = name

        device_types = {}
        for device in all_devices:
            name, device_type, status, _, _ = device
            device_list = device_types.setdefault(device_type, list())
            device_list.append({
                'name': name,
                'online': status in DEVICE_ONLINE_STATUS,
            })
        online_status = {
            device_type: any(device['online'] for device in devices)
            for device_type, devices in device_types.items()
        }

        return {
            'online_status': online_status,
            'aliases': all_aliases,
        }

    def _connect(self, user=None, token=None, **kwargs):
        """Connect to the remote server API

        *user* is the name of the user to connect to the lab
        *token* is the token associated with the user to connect to the lab
        """
        if user and token:
            url = urllib.parse.urlparse(self.config.url)
            api_url = "{scheme}://{user}:{token}@{loc}{path}".format(
                scheme=url.scheme, user=user, token=token,
                loc=url.netloc, path=url.path)
        else:
            api_url = self.config.url
        if api_url.strip()[-1] != '/':
            api_url = f'{api_url}/'
        self._server = xmlrpc.client.ServerProxy(api_url)
        return self._server

    def _alias_device_type(self, device_type):
        aliases = self.devices.get('aliases', dict())
        return aliases.get(device_type, device_type)

    def device_type_online(self, device_type_config):
        device_type = self._alias_device_type(device_type_config.base_name)
        online_status = self.devices.get('online_status', dict())
        return online_status.get(device_type, False)

    def _submit(self, job):
        return self._server.scheduler.submit_job(job)


def get_runtime(runtime_config, **kwargs):
    """Get a LAVA runtime object"""
    return LAVA(runtime_config, **kwargs)
