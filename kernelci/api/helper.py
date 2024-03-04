# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI API helpers"""

from typing import Dict
import json
import requests

from . import API


def merge(primary: dict, secondary: dict):
    """Deep merges dicts a and b, returning a new dict containing
    dictionary a updated with the contents of dictionary b.
    TODO: This might need to be moved elsewhere, with proper fix to
    https://github.com/kernelci/kernelci-core/issues/2386
    """
    result = {}
    for key in primary:
        result[key] = primary[key]
        if key in secondary:
            if isinstance(primary[key], dict) and \
               isinstance(secondary[key], dict):
                result[key] = merge(primary[key], secondary[key])
            else:
                result[key] = secondary[key]
    for key in secondary:
        if key not in primary:
            result[key] = secondary[key]
    return result


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

    def _find_container(self, field, node):
        """
        Return the first found dict containing a field of a given name
        """
        for item in node:
            if isinstance(node[item], dict):
                base_object = self._find_container(field, node[item])
                if base_object:
                    return base_object
            elif field == item:
                return node
        return None

    # pylint: disable=too-many-arguments
    def _is_allowed(self, rules, key, node, parent, name):
        """
        Check whether the value of a specific node attribute matches
        a filtering rule. As the specified attribute might not be present
        in the node being created, we fall back to checking the value in its
        parent node in such cases.

        Returns True if the rule allows the current value, False otherwise.
        """

        # Find the node (or parent node) attribute corresponding to the
        # rule we're applying
        base = self._find_container(key, node)
        if not base:
            base = self._find_container(key, parent)
        if not base:
            return True

        block = [f.lstrip('!') for f in rules[key] if f.startswith('!')]
        allow = [f for f in rules[key] if not f.startswith('!')]

        # Rules are appied depending on how the data is initially stored:
        # * if it's a list (e.g. config fragments), then it must contain
        #   at least one element from the allow-list; additionally, none
        #   of the list elements can be part of the block-list
        # * if it's a single object (likely a string), then it must be
        #   present in the allow-list and absent from the block-list
        if isinstance(base[key], list):
            found = False

            # If the allow-list is empty, we assume no value is required and
            # will only return False if one of the elements is in the
            # block-list
            if len(allow) == 0:
                found = True

            for item in base[key]:
                if item in block:
                    print(f"{key.capitalize()} {item} not allowed for {name}")
                    return False
                if item in allow:
                    found = True

            if not found:
                print(f"{key.capitalize()} missing one of {allow} for {name}")
                return False

        else:
            if base[key] in block or (len(allow) > 0 and base[key] not in allow):
                print(f"{key.capitalize()} {base[key]} not allowed for {name}")
                return False

        return True

    def _should_create_node(self, node, parent, config):
        """
        Check whether a node should be created based on configured rules.
        Those can be specified in the job, platform or runtime configuration
        and affect any field in the node structure. Rules can specify a list of
        allowed values and blocked ones as well (prepending the value with `!`
        in the latter case).Rules should be formatted as follows:

          rules:
            field1:
              - 'allowed-value1'
              - 'allowed-value2'
              ...
              - '!blocked-value1'
              - '!blocked-value2'
              ...

        An additional rule can be defined to check for a minimum kernel version,
        formatted as follows:

            min_version:
              version: int # major version
              patchlevel: int # minor version

        For example, a job can be configured to run only on arm64 devices, with
        a kernel version >= 6.6, built with any defconfig except `allnoconfig`,
        and using the `kselftest` fragment but not the `arm64-chromebook` one,
        by adding the following to the job definition:

          rules:
            min_version:
              version: 6
              patchlevel: 6
            arch:
              - 'arm64'
            defconfig:
              - '!allnoconfig'
            fragments:
              - 'kselftest'
              - '!arm64-chromebook'
        """
        if config.rules is None:
            return True

        for key in config.rules:
            # Special case as there is no field in the node giving us the full
            # kernel version in "x.y" format
            if key == 'min_version':
                kver = node['data']['kernel_revision']['version']
                major = kver['version']
                minor = kver['patchlevel']
                rule_major = config.rules[key]['version']
                rule_minor = config.rules[key]['patchlevel']
                if (major < rule_major) or (major == rule_major and minor < rule_minor):
                    print(f"Version {major}.{minor} older than minimum version for "
                          f"{config.name} ({rule_major}.{rule_minor})")
                    return False

            elif not self._is_allowed(config.rules, key, node, parent, config.name):
                return False

        return True

    def create_job_node(self, job_config, input_node,
                        runtime=None, platform=None):
        """Create a new job node based on input and configuration"""
        job_node = {
            'kind': job_config.kind,
            'parent': input_node['id'],
            'name': job_config.name,
            'path': input_node['path'] + [job_config.name],
            'group': job_config.name,
            'artifacts': input_node['artifacts'],
            'data': {
                'kernel_revision': input_node['data']['kernel_revision'],
            },
        }
        if not self._should_create_node(job_node, input_node, job_config):
            print("Not creating node due to job rules")
            return None
        # Test-specific fields inherited from parent node (kbuild or
        # test) if available
        if job_config.kind == 'test':
            job_node['data']['kernel_type'] = input_node['data'].get('kernel_type')
            job_node['data']['arch'] = input_node['data'].get('arch')
            job_node['data']['defconfig'] = input_node['data'].get('defconfig')
            job_node['data']['config_full'] = input_node['data'].get('config_full')
            job_node['data']['compiler'] = input_node['data'].get('compiler')
        # This information is highly useful, as we might
        # extract from it the following, for example:
        # in case of lab: lab-name, device-name
        # in case of kubernetes: cluster name
        if runtime:
            job_node['data']['runtime'] = runtime.config.name
            if not self._should_create_node(job_node, input_node, runtime.config):
                print("Not creating node due to runtime rules")
                return None
        if platform:
            job_node['data']['platform'] = platform.name
            if not self._should_create_node(job_node, input_node, platform):
                print("Not creating node due to platform rules")
                return None
        try:
            return self._api.node.add(job_node)
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(json.loads(error.response.content)) from error

    def submit_regression(self, regression):
        """Post a regression object

        [TODO] Leave this function in place in case we'll need any other
        processing or formatting before submitting the regression node
        """
        # pylint: disable=protected-access
        try:
            return self.api._post('node', regression)
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(json.loads(error.response.content)) from error

    def _prepare_results(self, results, parent, base):
        node = results['node'].copy()
        # Merge `Node.data` instead of overwriting it
        for key, value in base.items():
            if isinstance(value, dict):
                if node.get(key):
                    node[key].update(value)
                else:
                    node.update({key: value})
            else:
                node[key] = value
        node['path'] = (parent['path'] if parent else []) + [node['name']]
        if 'kind' not in node:
            node['kind'] = parent['kind']
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
        Logic need fix:
        https://github.com/kernelci/kernelci-core/issues/2386
        """
        root_from_db = self.api.node.get(root['id'])
        root_node = merge(root_from_db, root)
        root_node = root.copy()
        root_node['result'] = results['node']['result']
        root_node['artifacts'].update(results['node']['artifacts'])
        root_results = {
            'node': root_node,
            'child_nodes': results['child_nodes'],
        }
        parent = self.api.node.get(root['parent'])
        base = {
            'data': {
                'kernel_revision': root['data'].get('kernel_revision'),
                'kernel_type': root['data'].get('kernel_type'),
                'arch': root['data'].get('arch'),
                'defconfig': root['data'].get('defconfig'),
                'config_full': root['data'].get('config_full'),
                'compiler': root['data'].get('compiler'),
                'platform': root['data'].get('platform'),
                'runtime': root['data'].get('runtime'),
            },
            'group': root['name'],
            'state': 'done',
        }
        data = self._prepare_results(root_results, parent, base)
        # Once this has been consolidated at the API level:
        # self.api.create_node_hierarchy(data)
        node_id = data['node']['id']
        # pylint: disable=protected-access
        try:
            return self.api._put(f'nodes/{node_id}', data).json()
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(json.loads(error.response.content)) from error

    @classmethod
    def load_json(cls, json_path, encoding='utf-8'):
        """Read content from JSON file"""
        with open(json_path, encoding=encoding) as json_file:
            return json.load(json_file)
