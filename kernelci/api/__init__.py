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


class Data:
    """Convenience class to keep common data in API bindings implementation"""

    def __init__(self, config: kernelci.config.api.API, token: str):
        self._config = config
        self._token = token
        self._headers = {'Content-Type': 'application/json'}
        if self._token:
            self._headers['Authorization'] = f'Bearer {self._token}'
        self._timeout = float(config.timeout)

    @property
    def config(self) -> kernelci.config.api.API:
        """API config object"""
        return self._config

    @property
    def timeout(self) -> float:
        """Timeout duration in seconds"""
        return self._timeout

    @property
    def headers(self) -> dict:
        """HTTP headers with content type, authorization token etc."""
        return self._headers


class Base:
    """Common primitive methods used in API bindings implementation"""

    def __init__(self, data: Data):
        self._data = data

    @property
    def data(self) -> Data:
        """Internal Data object instance"""
        return self._data

    def make_url(self, path: str) -> str:
        """Make a full URL for a given API endpoint path"""
        version_path = '/'.join((self.data.config.version, path))
        return urllib.parse.urljoin(self.data.config.url, version_path)

    def _get(self, path, params=None):
        url = self.make_url(path)
        resp = requests.get(
            url, params, headers=self.data.headers,
            timeout=self.data.timeout
        )
        resp.raise_for_status()
        return resp

    def _post(self, path, data=None, params=None, json_data=True):
        url = self.make_url(path)
        if json_data:
            jdata = json.dumps(data)
            resp = requests.post(
                url, jdata, headers=self.data.headers,
                params=params, timeout=self.data.timeout
            )
        else:
            headers = self.data.headers.copy()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            resp = requests.post(
                url, data, headers=headers,
                params=params, timeout=self.data.timeout
            )
        resp.raise_for_status()
        return resp

    def _put(self, path, data=None, params=None):
        url = self.make_url(path)
        jdata = json.dumps(data)
        resp = requests.put(
            url, jdata, headers=self.data.headers,
            params=params, timeout=self.data.timeout
        )
        resp.raise_for_status()
        return resp

    def _patch(self, path, data=None, params=None):
        url = self.make_url(path)
        jdata = json.dumps(data)
        resp = requests.patch(
            url, jdata, headers=self.data.headers,
            params=params, timeout=self.data.timeout
        )
        resp.raise_for_status()
        return resp


class API(abc.ABC, Base):  # pylint: disable=too-many-public-methods
    """KernelCI API Python bindings abstraction"""

    def __init__(self, config: kernelci.config.api.API, token: str):
        data = Data(config, token)
        Base.__init__(self, data)

    @property
    def config(self) -> kernelci.config.api.API:
        """API configuration data"""
        return self.data.config

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

    @abc.abstractmethod
    def create_token(self, username: str, password: str) -> dict:
        """Create a new API token for the current user"""

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

    # -------------
    # User accounts
    # -------------

    @abc.abstractmethod
    def get_users(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        """Get user accounts that match the provided attributes"""

    @abc.abstractmethod
    def create_user(self, user: dict) -> dict:
        """Create a new user"""

    @abc.abstractmethod
    def update_user(self, fields: dict, user_id: Optional[str] = None) -> dict:
        """Update a user matching the given user id with the provided fields

        The `fields` dictionary contains a subset of the key/value pairs to
        update in the user data.  If `user_id` is `None` then the current user
        associated with the API token in the request will be used by default.
        Updating other users requires superuser permission.
        """

    @abc.abstractmethod
    def request_verification_token(self, email: str):
        """Request email verification token"""

    @abc.abstractmethod
    def verify_user(self, token: str):
        """Verify user's email address"""

    @abc.abstractmethod
    def request_password_reset_token(self, email: str):
        """Request password reset token"""

    @abc.abstractmethod
    def reset_password(self, token: str, password: str):
        """Reset password"""

    @abc.abstractmethod
    def get_user(self, user_id: str) -> dict:
        """Get the user matching the given user id"""

    @abc.abstractmethod
    def update_password(self, username: str, current_password: str,
                        new_password: str):
        """Update password"""


def get_api(config, token=None):
    """Get a KernelCI API object matching the provided configuration"""
    version = config.version
    mod = importlib.import_module('.'.join(['kernelci', 'api', version]))
    api = mod.get_api(config, token)
    return api
