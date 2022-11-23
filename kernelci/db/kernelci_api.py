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

import json
import requests
import urllib.parse

from cloudevents.http import from_json

from kernelci.db import Database


class KernelCI_API(Database):

    def __init__(self, config, token):
        super().__init__(config, token)
        if self._token is None:
            raise ValueError("API token required for kernelci_api")
        self._headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json',
        }
        self._filters = {}

    def _make_url(self, path):
        return urllib.parse.urljoin(self.config.url, path)

    def _print_http_error(self, http_error, verbose=False):
        print(http_error)
        if verbose:
            print("Error:",
                  json.loads(http_error.response.content).get("detail", []))

    def _get(self, path, params=None):
        url = self._make_url(path)
        resp = requests.get(url, params=params, headers=self._headers)
        resp.raise_for_status()
        return resp

    def _post(self, path, data=None):
        url = self._make_url(path)
        resp = requests.post(url, headers=self._headers, data=data)
        resp.raise_for_status()
        return resp

    def _put(self, path, data=None):
        url = self._make_url(path)
        resp = requests.put(url, headers=self._headers, data=data)
        resp.raise_for_status()
        return resp

    def subscribe(self, channel):
        resp = self._post(f'subscribe/{channel}')
        return json.loads(resp.text)['id']

    def subscribe_node_channel(self, filters=None):
        resp = self._post(f'subscribe/node')
        sub_id = json.loads(resp.text)['id']
        self._filters[sub_id] = filters
        return sub_id

    def unsubscribe(self, sub_id):
        if sub_id in self._filters:
            self._filters.pop(sub_id)
        self._post(f'unsubscribe/{sub_id}')

    def get_event(self, sub_id):
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

    def count_nodes(self, attributes: dict = None):
        """Get the count of all nodes matching attributes"""
        resp = self._get('count', params=attributes)
        return resp.json()

    def get_node(self, node_id):
        resp = self._get('/'.join(['node', node_id]))
        return json.loads(resp.text)

    def get_nodes(self, attributes: dict = None,
                  offset: int = None, limit: int = None):
        """Get all nodes matching attributes"""
        params = attributes.copy() if attributes else {}

        if any((offset, limit)):
            params.update({
                'offset': offset or None,
                'limit': limit or None,
            })
            resp = self._get('nodes', params=params)
            return resp.json()['items']

        offset = 0
        limit = 100
        params['limit'] = limit
        nodes = []
        while True:
            params['offset'] = offset
            resp = self._get('nodes', params=params)
            items = resp.json()['items']
            nodes.extend(items)
            if len(items) < limit:
                break
            offset += limit
        return nodes

    def get_node_from_event(self, event):
        return self.get_node(event.data['id'])

    def get_root_node(self, node_id):
        resp = self._get('/'.join(['get_root_node', node_id]))
        return json.loads(resp.text)

    def get_regressions_by_node_id(self, node_id):
        """ Get a list of regressions matching node_id"""
        params = {
            "kind": "regression",
            "parent": node_id
        }
        resp = self._get('nodes', params=params)
        return resp.json()

    def pubsub_event_filter(self, sub_id, event):
        """Filter Pub/Sub events

        Filter received Pub/Sub event using provided filter dictionary.
        Return True if client has not provided any filter dictionary.
        If filters are provided, return True if the event data matches with
        the filter parameters, otherwise False.
        """
        filters = self._filters.get(sub_id)
        if not filters:
            return True
        for key, value in filters.items():
            if key not in event.keys():
                continue
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in event.get(key):
                        continue
                    if isinstance(sub_value, tuple):
                        if not any(sub_sub_value == event.get(key).get(sub_key)
                                   for sub_sub_value in sub_value):
                            return False
                    elif sub_value != event.get(key).get(sub_key):
                        return False
            elif isinstance(value, tuple):
                if not any(sub_value == event[key] for sub_value in value):
                    return False
            elif value != event[key]:
                return False

        return True

    def receive_node(self, sub_id):
        """
        Listen to all the events on 'node' channel and apply filter on it.
        Return node if event matches with the filter.
        """
        while True:
            event = self.get_event(sub_id)
            node = self.get_node_from_event(event)
            if all(self.pubsub_event_filter(sub_id, obj) for obj in [
                                                                node,
                                                                event.data]):
                return node

    def submit(self, data, verbose=False):
        obj_list = []
        for path, item in data.items():
            try:
                node_id = item.get('_id')
                if node_id:
                    resp = self._put(f"{path}/{node_id}", json.dumps(item))
                else:
                    resp = self._post(path, json.dumps(item))
            except requests.exceptions.HTTPError as ex:
                self._print_http_error(ex, verbose)
                raise(ex)
            obj = json.loads(resp.text)
            obj_list.append(obj)
        return obj_list

    def _prepare_results(self, results, parent, base):
        node = results['node'].copy()
        node.update(base)
        node['path'] = (parent['path'] if parent else []) + [node['name']]
        child_nodes = []
        for child_node in results['child_nodes']:
            child_nodes.append(self._prepare_results(child_node, node, base))
        return {
            'node': node,
            'child_nodes': child_nodes,
        }

    def submit_results(self, results, root, path='nodes', verbose=False):
        """Submit a hierarchy of results

        Submit a hierarchy of test results with 'node' containing data for a
        particular result or parent entry for sub-tests and 'child_nodes'
        containing a list of sub-results.  The root node needs to have been
        previously retrieved from the API with an existing _id.
        """
        parent = self.get_node(root['parent'])
        base = {
            'revision': root['revision'],
            'group': root['name'],
            'state': 'done',
        }
        root_node = results['node'].copy()
        root_node.update({
            '_id': root['_id'],
            'parent': root['parent'],
        })
        root_results = {
            'node': root_node,
            'child_nodes': results['child_nodes'],
        }
        data = self._prepare_results(root_results, parent, base)
        try:
            node_id = data['node']['_id']
            resp = self._put(f'{path}/{node_id}', json.dumps(data))
        except requests.exceptions.HTTPError as ex:
            self._print_http_error(ex, verbose)
            raise(ex)
        return json.loads(resp.text)


def get_db(config, token):
    """Get a KernelCI API database object"""
    return KernelCI_API(config, token)
