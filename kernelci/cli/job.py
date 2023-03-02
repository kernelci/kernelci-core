# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to generate and run KernelCI jobs"""

from .base import APICommand, Args, sub_main


class cmd_register(APICommand):  # pylint: disable=invalid-name
    """Create a new node before running a job"""
    args = APICommand.args + [Args.plan]

    opt_args = APICommand.opt_args + [
        Args.indent,
        {
            'name': '--input-node-id',
            'help': "ID of the input node",
        },
        {
            'name': '--input-node-json',
            'help': "Alternatively, path to the input node JSON file",
        },
        {
            'name': '--id-only',
            'action': 'store_true',
            'help': "Only print the node ID rather than the full node data",
        },
    ]

    # This should in fact be using a generic method in the API class
    # pylint: disable=no-self-use
    def _create_node(self, api, input_node, plan_config):
        job_node = {
            'parent': input_node['_id'],
            'name': plan_config.name,
            'path': input_node['path'] + [plan_config.name],
            'group': plan_config.name,
            'artifacts': input_node['artifacts'],
            'revision': input_node['revision'],
        }
        return api.submit({'node': job_node})[0]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        if args.input_node_id:
            input_node = api.get_node(args.input_node_id)
        elif args.input_node_json:
            input_node = self._load_json(args.input_node_json)
        else:
            print("\
Invalid arguments.  Either --input-node-id or --input-node-json is required.")
            return False
        plan_config = configs['test_plans'][args.plan]
        node = self._create_node(api, input_node, plan_config)
        if args.id_only:
            print(node['_id'])
        else:
            self._print_json(node, args.indent)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("job", globals(), args)
