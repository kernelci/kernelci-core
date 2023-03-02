# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
# Guillaume Tucker <guillaume.tucker@collabora.com>

from collections import namedtuple
import json
import requests
from urllib.parse import urljoin
import yaml

from . import LavaRuntime

RestAPIServer = namedtuple('RestAPIServer', ['url', 'session'])


class LavaRest(LavaRuntime):
    """Interface to a LAVA lab

    This implementation of kernelci.runtime.LabAPI is to communicate with LAVA
    labs.  It can retrieve some information such as the list of devices and
    their online status, generate and submit jobs with callback parameters.
    One special thing it can deal with is job priorities, which is only
    available in kernelci.config.runtime.lab_LAVA objects.
    """
    API_VERSION = 'v0.2'

    def _get_response(self, url):
        resp = self._server.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def _get_all(self, url):
        resp = self._get_response(url)
        results = resp['results']
        while resp['next']:
            resp = self._get_response(resp['next'])
            results.extend(resp['results'])
        return results

    def _get_devices(self):
        devices_url = urljoin(self._server.url, 'devices')
        aliases_url = urljoin(self._server.url, 'aliases')
        all_devices = self._get_all(devices_url)
        all_aliases = {item['name']: item['device_type']
                       for item in self._get_all(aliases_url)}
        device_types = {}
        for device in all_devices:
            device_list = device_types.setdefault(
                device['device_type'], list())
            device_list.append({
                'name': device['hostname'],
                'online': device['health'] == 'Good',
            })
        online_status = {
            device_type: any(device['online'] for device in devices)
            for device_type, devices in device_types.items()
        }

        return {
            'online_status': online_status,
            'aliases': all_aliases,
        }

    def _alias_device_type(self, device_type):
        aliases = self.devices.get('aliases', dict())
        return aliases.get(device_type, device_type)

    def _connect(self, token=None, **kwargs):
        """Connect to the remote server API

        *token* is the token associated with the user to connect to the lab
        """
        rest_headers = {
            'authorization': f'Token {token}',
            'content-type': 'application/json'
        }
        rest_url = f'{self.config.url}/api/{self.API_VERSION}/'
        rest_api = RestAPIServer(rest_url, requests.Session())
        rest_api.session.params = {'format': 'json', 'limit': '256'}
        rest_api.session.headers = rest_headers
        return rest_api

    def device_type_online(self, device_type_config):
        device_type = self._alias_device_type(device_type_config.base_name)
        online_status = self.devices.get('online_status', dict())
        return online_status.get(device_type, False)

    def _submit(self, job):
        jobs_url = urljoin(self._server.url, 'jobs/')
        job_data = {
            'definition': yaml.dump(yaml.load(job, Loader=yaml.CLoader)),
        }
        resp = self._server.session.post(jobs_url, json=job_data,
                                         allow_redirects=False)
        resp.raise_for_status()
        return resp.json()['job_ids'][0]


def get_runtime(runtime_config, **kwargs):
    """Get a lavaRest runtime object"""
    return LavaRest(runtime_config, **kwargs)
