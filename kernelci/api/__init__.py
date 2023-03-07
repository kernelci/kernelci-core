# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API"""

import abc
import enum
import importlib
import json
import urllib

import requests

import kernelci.config.api


class API(abc.ABC):
    """Base class for the KernelCI API Python bindings"""

    def __init__(self, config: kernelci.config.api.API, token: str):
        self._config = config
        self._token = token
        self._headers = {'Content-Type': 'application/json'}
        if self._token:
            self._headers['Authorization'] = f'Bearer {self._token}'

    @property
    def config(self) -> kernelci.config.api.API:
        """API configuration data"""
        return self._config

    # -------------------------------------------------------------------------
    # Abstract interface to be implemented
    #

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """API version"""

    @property
    @abc.abstractmethod
    def node_states(self):
        """An enum with all the valid node state names"""

    @abc.abstractmethod
    def hello(self) -> dict:
        """Get the hello message"""

    @abc.abstractmethod
    def whoami(self) -> dict:
        """Get information about the current user"""

    # -------------------------------------------------------------------------
    # Private methods
    #

    def _make_url(self, path):
        version_path = '/'.join((self.config.version, path))
        return urllib.parse.urljoin(self.config.url, version_path)

    def _get(self, path, params=None):
        url = self._make_url(path)
        resp = requests.get(url, params, headers=self._headers)
        resp.raise_for_status()
        return resp

    def _post(self, path, data=None, params=None):
        url = self._make_url(path)
        jdata = json.dumps(data)
        resp = requests.post(url, jdata, headers=self._headers, params=params)
        resp.raise_for_status()
        return resp

    def _put(self, path, data=None, params=None):
        url = self._make_url(path)
        jdata = json.dumps(data)
        resp = requests.put(url, jdata, headers=self._headers, params=params)
        resp.raise_for_status()
        return resp


def get_api(config, token=None):
    """Get a KernelCI API object matching the provided configuration"""
    version = config.version
    mod = importlib.import_module('.'.join(['kernelci', 'api', version]))
    api = mod.get_api(config, token)
    return api
