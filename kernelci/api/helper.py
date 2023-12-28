# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI API helpers"""

from typing import Dict
import json

from . import API


class APIHelper:
    """API helper base class

    This provides some common middleware between the API class and
    applications.
    """

    def __init__(self, api: API):
        self._api = api
        self._filters: Dict[str, Dict[str, str]] = {}

    @property
    def api(self):
        """API object"""
        return self._api

    def subscribe_filters(self, filters=None, channel='node'):
        """Subscribe to a channel with some added filters"""
        sub_id = self.api.subscribe(channel)
        self._filters[sub_id] = filters
        return sub_id

    def unsubscribe_filters(self, sub_id):
        """Unsubscribe from a channel with previously registered filters"""
        if sub_id in self._filters:
            self._filters.pop(sub_id)
        self.api.unsubscribe(sub_id)

    def receive_event_data(self, sub_id):
        """Receive CloudEvent from Pub/Sub and return its data payload"""
        return self.api.receive_event(sub_id).data

    def pop_event_data(self, list_name):
        """Receive CloudEvent from Redis list and return its data payload"""
        return self.api.pop_event(list_name).data

    def get_node_from_event(self, event_data):
        """Listen for an event and get the matching node object from it"""
        if 'id' in event_data:
            return self.api.node.get(event_data['id'])
        return None

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

    def receive_event_node(self, sub_id):
        """
        Listen to all the events on 'node' channel and apply filter on it.
        Return node if event matches with the filter.
        """
        while True:
            event = self.receive_event_data(sub_id)
            node = self.get_node_from_event(event)
            # Crude (provisional) filtering of non-node events
            if not node:
                continue
            if all(self.pubsub_event_filter(sub_id, obj)
                   for obj in [node, event]):
                return node

    def create_job_node(self, job_config, input_node,
                        runtime=None, platform=None):
        """Create a new job node based on input and configuration"""
        job_node = {
            'parent': input_node['id'],
            'name': job_config.name,
            'path': input_node['path'] + [job_config.name],
            'group': job_config.name,
            'artifacts': input_node['artifacts'],
            'revision': input_node['revision'],
        }
        # This information is highly useful, as we might
        # extract from it the following, for example:
        # in case of lab: lab-name, device-name
        # in case of kubernetes: cluster name
        if runtime:
            job_node['data'] = {'runtime': runtime.config.name}
        if platform:
            if 'data' not in job_node:
                job_node['data'] = {}
            job_node['data']['platform'] = platform.name
        return self._api.node.add(job_node)

    def submit_regression(self, regression):
        """Post a regression object

        It is still unclear whether regressions should have their own separate
        endpoint or just be added to the nodes collection with a different
        'kind' field.  For now, treat this as a middleware feature on top of
        the established API endpoints.
        """
        # pylint: disable=protected-access
        return self.api._post('regression', regression)

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

    def submit_results(self, results, root):
        """Submit a hierarchy of results

        Submit a hierarchy of test results with 'node' containing data for a
        particular result or parent entry for sub-tests and 'child_nodes'
        containing a list of sub-results.  The root node needs to have been
        previously retrieved from the API with an existing id.

        `root` is the root node for all the child results
        `results` are the child results with the following recursive format:
        {
            "node": {
                "name": "group name",
                "result": "pass",
            },
            "child_nodes": [
                {
                    "node": {
                        "name": "test name",
                        "result": "fail",
                    },
                    "child_nodes": [],
                }
            ]
        }
        """
        root_node = root.copy()
        root_node['result'] = results['node']['result']
        root_node['artifacts'].update(results['node']['artifacts'])
        root_results = {
            'node': root_node,
            'child_nodes': results['child_nodes'],
        }
        parent = self.api.node.get(root['parent'])
        base = {
            'revision': root['revision'],
            'group': root['name'],
            'state': 'done',
        }
        data = self._prepare_results(root_results, parent, base)
        # Once this has been consolidated at the API level:
        # self.api.create_node_hierarchy(data)
        node_id = data['node']['id']
        # pylint: disable=protected-access
        return self.api._put(f'nodes/{node_id}', data).json()

    @classmethod
    def load_json(cls, json_path, encoding='utf-8'):
        """Read content from JSON file"""
        with open(json_path, encoding=encoding) as json_file:
            return json.load(json_file)
