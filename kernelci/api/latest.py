# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API bindings for the latest version"""

import enum
from typing import Optional, Sequence

from cloudevents.http import from_json
import requests

from . import API


class NodeStates(enum.Enum):
    """Node states names"""
    RUNNING = 'running'
    AVAILABLE = 'available'
    CLOSING = 'closing'
    DONE = 'done'


class LatestAPI(API):
    """Latest API version

    The 'latest' version is used to refer to the current development version,
    so it's not pinned down.  It's a moving target and shouldn't be used in
    production environments.
    """

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def node_states(self):
        return NodeStates

    @property
    def security_scopes(self) -> Sequence[str]:
        return ['users', 'admin']

    def hello(self) -> dict:
        return self._get('/').json()

    def whoami(self) -> dict:
        return self._get('/whoami').json()

    def password_hash(self, password: str) -> dict:
        return self._post('/hash', {'password': password}).json()

    def create_token(self, username: str, password: str,
                     scopes: Optional[Sequence[str]] = None) -> str:
        data = {
            'username': username,
            'password': password,
        }
        # The form field name is scope (in singular), but it is actually a long
        # string with "scopes" separated by spaces.
        # https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/#scope
        if scopes:
            data['scope'] = ' '.join(scopes)
        url = self._make_url('/token')
        resp = requests.post(url, data)
        resp.raise_for_status()
        return resp.json()

    def subscribe(self, channel: str) -> int:
        resp = self._post(f'subscribe/{channel}')
        return resp.json()['id']

    def unsubscribe(self, sub_id: int):
        self._post(f'unsubscribe/{sub_id}')

    def send_event(self, channel: str, data):
        self._post('/'.join(['publish', channel]), data)

    def receive_event(self, sub_id: int):
        path = '/'.join(['listen', str(sub_id)])
        while True:
            resp = self._get(path)
            data = resp.json().get('data')
            if not data:
                continue
            event = from_json(data)
            if event.data == 'BEEP':
                continue
            return event

    def _get_api_objs(self, params: dict, path: str,
                      limit: Optional[int] = None,
                      offset: Optional[int] = None) -> list:
        """Helper function for getting objects from API with pagination
        parameters"""
        objs = []
        if any((offset, limit)):
            params.update({
                'offset': offset or None,
                'limit': limit or None,
            })
            resp = self._get(path, params=params)
            objs = resp.json()['items']
        else:
            offset = 0
            limit = 100
            params['limit'] = limit
            while True:
                params['offset'] = offset
                resp = self._get(path, params=params)
                items = resp.json()['items']
                objs.extend(items)
                if len(items) < limit:
                    break
                offset += limit
        return objs

    def get_node(self, node_id: str) -> dict:
        return self._get(f'node/{node_id}').json()

    def get_nodes(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        params = attributes.copy() if attributes else {}
        return self._get_api_objs(params=params, path='nodes',
                                  limit=limit, offset=offset)

    def count_nodes(self, attributes: dict) -> int:
        return self._get('count', params=attributes).json()

    def create_node(self, node: dict) -> dict:
        return self._post('node', node).json()

    def update_node(self, node: dict) -> dict:
        return self._put('/'.join(['node', node['id']]), node).json()

    def get_group(self, group_id: str) -> dict:
        return self._get(f'group/{group_id}').json()

    def get_groups(
        self, attributes: dict,
        offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Sequence[dict]:
        params = attributes.copy() if attributes else {}
        return self._get_api_objs(params=params, path='groups',
                                  limit=limit, offset=offset)


def get_api(config, token):
    """Get an API object for the latest version"""
    return LatestAPI(config, token)
