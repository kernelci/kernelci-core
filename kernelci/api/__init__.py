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
from typing import Optional, Sequence

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

    @property
    @abc.abstractmethod
    def security_scopes(self) -> Sequence[str]:
        """All the user token security scope names"""

    @abc.abstractmethod
    def hello(self) -> dict:
        """Get the hello message"""

    @abc.abstractmethod
    def whoami(self) -> dict:
        """Get information about the current user"""

    @abc.abstractmethod
    def password_hash(self, password: str) -> dict:
        """Get an encryption hash for a given password"""

    @abc.abstractmethod
    def create_token(self, username: str, password: str,
                     scopes: Optional[Sequence[str]] = None) -> str:
        """Create a new API token for the current user

        `scopes` contains optional security scope names which needs to be part
        of API.security_scopes.  Please note that user permissions can limit
        the available scopes, for example only admin users can create admin
        tokens.
        """

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
