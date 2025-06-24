# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2024 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

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

    def subscribe_filters(self, filters=None, channel='node',
                          promiscuous=False):
        """Subscribe to a channel with some added filters"""
        sub_id = self.api.subscribe(channel, promiscuous)
        self._filters[sub_id] = filters
        return sub_id

    def unsubscribe_filters(self, sub_id):
        """Unsubscribe from a channel with previously registered filters"""
        if sub_id in self._filters:
            self._filters.pop(sub_id)
        self.api.unsubscribe(sub_id)

    def receive_event_data(self, sub_id, block=True):
        """Receive CloudEvent from Pub/Sub and return its data payload
        If block is False, on receiving an "keep-alive" event,
        such as "BEEP" ping, it will return None instead of the data.
        Without this, it will block until an event is received.
        """
        event = self.api.receive_event(sub_id, block=block)
        if event is None:
            return None
        return event.data

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
                return node, event.get('is_hierarchy')

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
    def _is_allowed(self, rules, key, node, parent):
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
        if not base and parent:
            base = self._find_container(key, parent)
        if not base:
            return True

        deny = [f.lstrip('!') for f in rules[key] if f.startswith('!')]
        allow = [f for f in rules[key] if not f.startswith('!')]

        # Rules are appied depending on how the data is initially stored:
        # * if it's a list (e.g. config fragments), then it must contain
        #   at least one element from the allow-list; additionally, none
        #   of the list elements can be part of the deny-list
        # * if it's a single object (likely a string), then it must be
        #   present in the allow-list and absent from the deny-list
        if isinstance(base[key], list):
            found = False

            # If the allow-list is empty, we assume no value is required and
            # will only return False if one of the elements is in the
            # deny-list
            if len(allow) == 0:
                found = True

            for item in base[key]:
                if item in deny:
                    print(f"rules{key}: {key.capitalize()} {item} not allowed due {deny}")
                    return False
                if item in allow:
                    found = True

            if not found:
                print(f"rules: {key.capitalize()} missing one of {allow}")
                return False

        else:
            if base[key] in deny or (len(allow) > 0 and base[key] not in allow):
                print(f"rule[{key}]: {key.capitalize()} {base[key]} not allowed due {deny}")
                return False

        return True

    def _extract_combos(self, rules, key):
        """
        Process tree/branch rules and extract "combo" values.

        Tree and branch rules can be formatted as `<tree>:<branch>`, meaning
        only a given branch is allowed for a specific tree. When prepended with
        `!`, it indicates a forbidden tree/branch combination.

        In order to simplify further processing, this function processes those
        rules and returns lists of allowed/denied single values and combos.

        Returns a tuple of 4 arrays:
          * allowed single values
          * allowed combinations
          * denied single values
          * denied combinations
        """

        allow = []
        allow_combos = []
        deny = []
        deny_combos = []

        for rule in rules[key]:
            if ':' in rule:
                combo = {}
                # we use ':' as a tree/branch separator as this character is forbidden
                # in git branch names, so if found it should be present only once.
                [combo['tree'], combo['branch']] = rule.split(':', 1)
                if combo['tree'].startswith('!'):
                    combo['tree'] = combo['tree'].lstrip('!')
                    deny_combos.append(combo)
                else:
                    allow_combos.append(combo)
            else:
                if rule.startswith('!'):
                    deny.append(rule.lstrip('!'))
                else:
                    allow.append(rule)

        return (allow, allow_combos, deny, deny_combos)

    def _match_combos(self, node, combos):
        """
        Check whether the current node's tree/branch attributes match one of the
        combinations present in combos.

        Returns the matched combo or None.
        """
        match = None
        for combo in combos:
            if node['tree'] == combo['tree'] and node['branch'] == combo['branch']:
                match = combo
                break
        return match

    def _is_tree_branch_allowed(self, node, rules):
        """
        Check whether the tree and/or branch for the current checkout matches
        the corresponding filtering rules.

        Returns True if the rules allow the current value, False otherwise.
        """
        for key in ("tree", "branch"):
            if key in rules:
                (allow, allow_combos, deny, deny_combos) = self._extract_combos(rules, key)
                # Process combos first:
                # * if the tree/branch combination matches an allowed combo, then the node
                #   fulfills the tree/branch rules and we can move forward to processing
                #   the other rules
                # * likewise, if the combination matches a denied combo, then we can stop
                #   processing here and reject the node creation altogether
                if self._match_combos(node, allow_combos):
                    break
                match = self._match_combos(node, deny_combos)
                if match:
                    print(f"Tree/branch combination "
                          f"{match['tree']}/{match['branch']} not allowed")
                    return False

                # Get back to regular allow/deny list processing
                if node[key] in deny:
                    print(f"{key.capitalize()} {node[key]} not allowed due {deny}")
                    return False
                if (len(allow) == 0 and len(allow_combos) > 0):
                    print(f"{key.capitalize()} {node[key]} not allowed due"
                          f" to tree/branch rules")
                    return False
                if (len(allow) > 0 and node[key] not in allow):
                    print(f"{key.capitalize()} {node[key]} not allowed due {allow}")
                    return False

        return True

    def should_create_node(self, rules, node, parent=None):
        """
        Check whether a node should be created based on configured rules.
        Those can be specified in the job, platform or runtime configuration
        and affect any field in the node structure. Rules can specify a list of
        allowed values and denied ones as well (prepending the value with `!`
        in the latter case).Rules should be formatted as follows:

          rules:
            field1:
              - 'allowed-value1'
              - 'allowed-value2'
              ...
              - '!denied-value1'
              - '!denied-value2'
              ...

        Additional rules can be defined to check for a minimum and/or maximum
        kernel version, formatted as follows:

            min_version:
              version: int # major version
              patchlevel: int # minor version

            max_version:
              version: int
              patchlevel: int

        For example, the following rules definition mean the job can run only:
          * with a kernel version between 6.1 and 6.6
          * on arm64 devices
          * when using a checkout from the `master` branch on the `linus` tree,
            or any branch except `master` on the `stable` tree
          * if the kernel has been built with any defconfig except `allnoconfig`,
            using the `kselftest` fragment but not the `arm64-chromebook` one

          rules:
            min_version:
              version: 6
              patchlevel: 1
            max_version:
              version: 6
              patchlevel: 6
            arch:
              - 'arm64'
            tree:
              - linus:master
              - stable
            branch:
              - '!stable:master'
            defconfig:
              - '!allnoconfig'
            fragments:
              - 'kselftest'
              - '!arm64-chromebook'
        """
        if rules is None:
            return True

        # Process the tree and branch rules first as they need specific processing
        # for handling tree/branch combinations

        # Find the node (or parent node) attribute containing the "tree" (and therefore
        # "branch") value
        ref_base = self._find_container("tree", node)
        if not ref_base and parent:
            ref_base = self._find_container("tree", parent)
        if ref_base and not self._is_tree_branch_allowed(ref_base, rules):
            return False

        for key in rules:
            # Skip tree and branch rules as we already processed them above
            if key in ("tree", "branch"):
                continue

            # Special case as there is no field in the node giving us the full
            # kernel version in "x.y" format
            if key.endswith('_version'):
                kver = node['data']['kernel_revision']['version']
                major = kver['version']
                minor = kver['patchlevel']
                rule_major = rules[key]['version']
                rule_minor = rules[key]['patchlevel']
                if (key.startswith('min') and
                    ((major < rule_major) or
                     (major == rule_major and minor < rule_minor))):
                    print(f"rules: Version {major}.{minor} older than minimum version "
                          f"({rule_major}.{rule_minor})")
                    return False
                if (key.startswith('max') and
                    ((major > rule_major) or
                     (major == rule_major and minor > rule_minor))):
                    print(f"rules: Version {major}.{minor} more recent than maximum version "
                          f"({rule_major}.{rule_minor})")
                    return False

            elif not self._is_allowed(rules, key, node, parent):
                return False

        return True

    def _fsanitize_node_fields(self, node, field_name):
        """
        Sanitize node fields to escape curly braces
        We need to walk over multiple levels of the node dict to find the field
        and escape the curly braces.
        """
        if isinstance(node, dict):
            for k, val in node.items():
                if k == field_name and isinstance(val, str):
                    node[k] = val.replace('}', '}}').replace('{', '{{')
                else:
                    self._fsanitize_node_fields(val, field_name)
        elif isinstance(node, list):
            for item in node:
                self._fsanitize_node_fields(item, field_name)
        return node

    def _is_job_filtered(self, node):
        """
        Check whether a node should be created based on the jobfilter list, if any.
        Jobs can be created in the following cases:
          * jobfilter explicitly contains the job name
          * jobfilter contains the name of either the job or one of its ancestors
            suffixed with a '+' sign.

        As an example, if jobfilter contains 'kbuild-job-x86' (and no other entry),
        then only the job named 'kbuild-job-x86' will be created. However, if this
        entry is changed to 'kbuild-job-x86+', then the listed kbuild job will be
        created, but also all of the (child) test jobs it would trigger.
        """
        jobfilter = node.get('jobfilter')
        # if jobfilter not null, first check node.name exists in jobfilter
        if jobfilter and node['name'] not in jobfilter:
            # now check whether one the following is true:
            #   * jobfilter contains the job name suffixed with '+'
            #   * at least one element of the node's 'path' appears in jobilfter
            #     with a '+' suffix
            for filt in (item.rstrip('+') for item in jobfilter if item.endswith('+')):
                if filt in node['path'] or filt == node['name']:
                    return False

            return True

        return False

    def create_job_node(self, job_config, input_node,
                        runtime=None, platform=None):
        """Create a new job node based on input and configuration"""
        jobfilter = input_node.get('jobfilter')
        platform_filter = input_node.get('platform_filter')
        treeid = input_node.get('treeid')
        submitter = input_node.get('submitter')
        job_node = {
            'kind': job_config.kind,
            'parent': input_node['id'],
            'name': job_config.name,
            'path': input_node['path'] + [job_config.name],
            'group': job_config.name,
            'artifacts': {},
            'treeid': treeid,
            'submitter': submitter,
            'data': {
                'kernel_revision': input_node['data']['kernel_revision'],
            },
        }
        if jobfilter:
            job_node['jobfilter'] = jobfilter
        if platform_filter:
            job_node['platform_filter'] = platform_filter

        if self._is_job_filtered(job_node):
            print(f"Filtered: Job {job_config.name} not found in jobfilter "
                  f"for node {input_node['id']}")
            return None

        if not self.should_create_node(job_config.rules, job_node, input_node):
            print(f"Not creating node due to job rules for {job_config.name} "
                  f"evaluating node {input_node['id']}")
            return None
        # Test-specific fields inherited from parent node (kbuild or
        # job) if available
        if job_config.kind == 'job':
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
            if not self.should_create_node(runtime.config.rules, job_node, input_node):
                print(f"Not creating node {input_node['id']} due to runtime rules "
                      f"for {runtime.config.name}")
                return None
        # Filter by platform if it is test job only
        if platform:
            # if platform_filter not null, verify if platform.name exist in platform_filter
            if platform_filter and platform.name not in platform_filter\
               and job_config.kind == 'job':
                print(f"Filtered: Platform {platform.name} not found in platform_filter "
                      f"for node {input_node['id']}")
                return None
            job_node['data']['platform'] = platform.name
            if not self.should_create_node(platform.rules, job_node, input_node):
                print(f"Not creating node {input_node['id']} due to platform rules "
                      f"for {platform.name}")
                return None
            # Process potential f-strings in node's data with platform attributes
            # krev is used for ChromeOS config version mapping
            kernel_revision = job_node['data']['kernel_revision']['version']
            extra_args = {
                'krev': f"{kernel_revision['version']}.{kernel_revision['patchlevel']}"
            }
            extra_args.update(job_config.params)
            # same time we need to make sure commit_message filtered from f-strings
            # as it is user supplied and might contain {} symbols
            job_node = self._fsanitize_node_fields(job_node, 'commit_message')

            try:
                job_node['data'] = platform.format_params(job_node['data'], extra_args)
            except Exception as error:
                print(f"Exception Error, node id: {input_node['id']}, {error}")
                raise error
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
        root_node['state'] = results['node'].get('state', 'done')
        if root_node.get('artifacts') is None:
            root_node['artifacts'] = {}
        root_node['artifacts'].update(results['node']['artifacts'])
        root_node['data'].update(results['node'].get('data', {}))
        root_node['processed_by_kcidb_bridge'] = False
        if 'holdoff' in results['node']:
            root_node['holdoff'] = results['node']['holdoff']
        if root_node['result'] != 'incomplete':
            data = root_node.get('data', {})
            if data.get('error_code') == 'node_timeout':
                root_node['data']['error_code'] = None
                root_node['data']['error_msg'] = None

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
            'processed_by_kcidb_bridge': False,
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

    def set_kv(self, namespace, key, value):
        """Set a key-value pair in the API"""
        try:
            return self.api.set_kv(namespace, key, value)
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(json.loads(error.response.content)) from error

    def get_kv(self, namespace, key):
        """Get a key-value pair from the API"""
        try:
            return self.api.get_kv(namespace, key)
        except requests.exceptions.HTTPError as error:
            raise RuntimeError(json.loads(error.response.content)) from error

    @classmethod
    def load_json(cls, json_path, encoding='utf-8'):
        """Read content from JSON file"""
        with open(json_path, encoding=encoding) as json_file:
            return json.load(json_file)
