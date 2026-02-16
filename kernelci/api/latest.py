# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023-2024 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""KernelCI API bindings for the latest version"""

import enum
import json
from typing import Dict, Optional, Sequence

from cloudevents.http import from_json

from . import API


class NodeStates(enum.Enum):
    """Node states names"""
    RUNNING = 'running'
    AVAILABLE = 'available'
    CLOSING = 'closing'
    DONE = 'done'


class LatestAPI(API):  # pylint: disable=too-many-public-methods
    """Latest API version

    The 'latest' version is used to refer to the current development version,
    so it's not pinned down.  It's a moving target and shouldn't be used in
    production environments.
    """

    @property
    def version(self) -> str:
        return self.config.version

    def hello(self) -> dict:
        return self._get('/').json()

    class User(API.User):
        """User bindings for the latest API version"""

        def whoami(self) -> dict:
            return self._get('/whoami').json()

        def create_token(self, username: str, password: str) -> dict:
            data = {
                'username': username,
                'password': password,
            }
            return self._post('/user/login', data, json_data=False).json()

        def get(self, user_id: str) -> dict:
            return self._get(f'user/{user_id}').json()

        def find(
            self, attributes: Dict[str, str],
            offset: Optional[int] = None, limit: Optional[int] = None
        ) -> Sequence[dict]:
            params = attributes.copy() if attributes else {}
            return self._get_paginated(params, 'users', offset, limit)

        def add(self, user: dict) -> dict:
            return self._post('user/register', user).json()

        def update(self, fields: dict, user_id: Optional[str] = None) -> dict:
            return self._patch(f'user/{user_id or "me"}', fields).json()

        def request_verification_token(self, email: str):
            return self._post('user/request-verify-token', {
                "email": email
            })

        def verify_email(self, token: str):
            return self._post('user/verify', {
                "token": token
            })

        def request_password_reset_token(self, email: str):
            return self._post('user/forgot-password', {
                "email": email
            })

        def reset_password(self, token: str, password: str):
            return self._post('user/reset-password', {
                "token": token,
                "password": password
            })

        def update_password(self, username: str, current_password: str,
                            new_password: str):
            data = {
                "username": username,
                "password": current_password,
                "new_password": new_password
            }
            return self._post('user/update-password', data, json_data=False)

    class Node(API.Node):
        """Node bindings for the latest API version"""

        @property
        def states(self):
            return NodeStates

        def get(self, node_id: str) -> dict:
            return self._get(f'node/{node_id}').json()

        def find(
            self, attributes: Dict[str, str],
            offset: Optional[int] = None, limit: Optional[int] = None
        ) -> Sequence[dict]:
            params = attributes.copy() if attributes else {}
            return self._get_paginated(params, 'nodes', offset, limit)

        def findfast(
            self, attributes: Dict[str, str],
        ) -> dict:
            """
            Find nodes with arbitrary attributes using non-paginated
            endpoint
            """
            params = attributes.copy() if attributes else {}
            return self._get_fast(params, 'nodes/fast')

        def count(self, attributes: dict) -> int:
            return self._get('count', params=attributes).json()

        def add(self, node: dict) -> dict:
            return self._post('node', node).json()

        def update(self, node: dict, noevent=False) -> dict:
            if node['result'] != 'incomplete':
                data = node.get('data', {})
                if data.get('error_code') == 'node_timeout':
                    node['data']['error_code'] = None
                    node['data']['error_msg'] = None
            uri = '/'.join(['node', node['id']])
            if noevent:
                uri += '?noevent=true'
            return self._put(uri, node).json()

        def bulkset(self, nodes: list, field: str, value: str):
            """
            Set a field to a value for a list of nodes(ids)
            """
            param = {
                'nodes': nodes,
                'field': field,
                'value': value
            }
            return self._put('batch/nodeset', data=param)

    class Telemetry(API.Telemetry):
        """Telemetry bindings for the latest API version"""

        def add(self, events: list) -> dict:
            """Bulk insert telemetry events"""
            return self._post('telemetry', events).json()

        def find(
            self, attributes: Dict[str, str],
            offset: Optional[int] = None, limit: Optional[int] = None
        ) -> Sequence[dict]:
            """Find telemetry events matching the provided attributes"""
            params = attributes.copy() if attributes else {}
            return self._get_paginated(params, 'telemetry', offset, limit)

        def stats(self, attributes: Dict[str, str]) -> list:
            """Return aggregated telemetry statistics for matched events.

            This endpoint only performs grouped aggregation of telemetry counters
            and does not perform anomaly detection.
            """
            params = attributes.copy() if attributes else {}
            return self._get('telemetry/stats', params=params).json()

    def subscribe(self, channel: str, promisc: Optional[bool] = None) -> int:
        params = {'promisc': promisc} if promisc else None
        resp = self._post(f'subscribe/{channel}', params=params)
        return resp.json()['id']

    def unsubscribe(self, sub_id: int):
        self._post(f'unsubscribe/{sub_id}')

    def send_event(self, channel: str, data):
        self._post('/'.join(['publish', channel]), data)

    def receive_event(self, sub_id: int, block: bool = True):
        path = '/'.join(['listen', str(sub_id)])
        while True:
            resp = self._get(path)
            data = resp.json().get('data')
            if not data:
                continue
            event = from_json(data)
            if event.data == 'BEEP':
                if not block:
                    # If block is False, return None
                    # for semi-nonblocking operation
                    return None
                continue
            return event

    def push_event(self, list_name: str, data):
        self._post('/'.join(['push', list_name]), data)

    def pop_event(self, list_name: str):
        path = '/'.join(['pop', str(list_name)])
        while True:
            resp = self._get(path)
            data = json.dumps(resp.json())
            event = from_json(data)
            return event

    def subscription_stats(self):
        return self._get('stats/subscriptions').json()

    def get_group(self, group_id: str) -> dict:
        return self._get(f'group/{group_id}').json()

    def get_groups(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        params = attributes.copy() if attributes else {}
        return self._get_paginated(params, 'groups', offset, limit)

    def create_group(self, name: str) -> dict:
        return self._post('group', {"name": name}).json()

    def delete_group(self, group_id: str):
        return self._delete(f'group/{group_id}')

    def set_kv(self, namespace: str, key: str, value: str):
        """
        Set a key-value pair in the database
        """
        return self._post(f'kv/{namespace}/{key}', value).json()

    def get_kv(self, namespace: str, key: str) -> str:
        """
        Get a value from the database
        """
        return self._get(f'kv/{namespace}/{key}').json()


def get_api(config, token):
    """Get an API object for the latest version"""
    return LatestAPI(config, token)
