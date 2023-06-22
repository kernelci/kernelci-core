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

from cloudevents.http import CloudEvent
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
        self._timeout = float(config.timeout)

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

    # -------
    # Pub/Sub
    # -------

    @abc.abstractmethod
    def subscribe(self, channel: str) -> int:
        """Subscribe to a pub/sub channel

        Subscribe to the given `channel` and get the subscription id.
        """

    @abc.abstractmethod
    def unsubscribe(self, sub_id: int):
        """Unsubscribe from the given subscription id"""

    @abc.abstractmethod
    def send_event(self, channel: str, data):
        """Send an event to a given pub/sub channel"""

    @abc.abstractmethod
    def receive_event(self, sub_id: int) -> CloudEvent:
        """Listen and receive an event from a given subscription id"""

    # -----
    # Nodes
    # -----

    @abc.abstractmethod
    def get_node(self, node_id: str) -> dict:
        """Get the node matching the given node id"""

    @abc.abstractmethod
    def get_nodes(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        """Get nodes that match the provided attributes"""

    @abc.abstractmethod
    def count_nodes(self, attributes: dict) -> int:
        """Count nodes that match the provided attributes"""

    @abc.abstractmethod
    def create_node(self, node: dict) -> dict:
        """Create a new node object (no id)"""

    @abc.abstractmethod
    def update_node(self, node: dict) -> dict:
        """Update an existing node object (with id)"""

    # -----------
    # User groups
    # -----------

    @abc.abstractmethod
    def get_group(self, group_id: str) -> dict:
        """Get the user group matching the given group id"""

    @abc.abstractmethod
    def get_groups(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        """Get user groups that match the provided attributes"""

    # -------------------------------------------------------------------------
    # Private methods
    #

    def _make_url(self, path):
        version_path = '/'.join((self.config.version, path))
        return urllib.parse.urljoin(self.config.url, version_path)

    def _get(self, path, params=None):
        url = self._make_url(path)
        resp = requests.get(
            url, params, headers=self._headers, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp

    def _post(self, path, data=None, params=None):
        url = self._make_url(path)
        jdata = json.dumps(data)
        resp = requests.post(
            url, jdata, headers=self._headers,
            params=params, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp

    def _put(self, path, data=None, params=None):
        url = self._make_url(path)
        jdata = json.dumps(data)
        resp = requests.put(
            url, jdata, headers=self._headers,
            params=params, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp


def get_api(config, token=None):
    """Get a KernelCI API object matching the provided configuration"""
    version = config.version
    mod = importlib.import_module('.'.join(['kernelci', 'api', version]))
    api = mod.get_api(config, token)
    return api
