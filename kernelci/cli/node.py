# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API node objects"""

import json
from kernelci.db import kernelci_api
from .base import Args, Command, sub_main


class NodeCommand(Command):  # pylint: disable=too-few-public-methods
    """Base command class for interacting with the KernelCI API"""
    args = [
        Args.api_config, Args.api_token,
    ]
    opt_args = [
        {
            'name': '--indent',
            'help': "Indentation string in output JSON",
        },
    ]

    @classmethod
    def _get_api(cls, configs, args):
        config = configs['api_configs'][args.api_config]
        return kernelci_api.KernelCI_API(config, args.api_token)

    def __call__(self, configs, args):
        pass


class NodeParamsCommand(NodeCommand):
    """Base command class for node queries with arbitrary parameters"""
    args = NodeCommand.args + [
        {
            'name': 'params',
            'nargs': '+',
            'help': "Parameters to find nodes in param=value format",
        },
    ]

    @classmethod
    def _split_params(cls, params):
        return dict(
            tuple(param.split('=')) for param in params
        )


class cmd_get(NodeCommand):  # pylint: disable=invalid-name
    """Get a node with a given ID"""
    args = NodeCommand.args + [
        {
            'name': 'id',
            'help': "Node id",
        },
    ]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        node = api.get_node(args.id)
        print(json.dumps(node, indent=args.indent))
        return True


class cmd_find(NodeParamsCommand):  # pylint: disable=invalid-name
    """Find nodes with arbitrary parameters"""
    opt_args = NodeParamsCommand.opt_args + [
        {
            'name': '--limit',
            'type': int,
            'help': "Maximum number of nodes to retrieve",
        },
        {
            'name': '--offset',
            'type': int,
            'help': "Offset when paginating results with a number of nodes",
        },
    ]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        params = self._split_params(args.params)
        nodes = api.get_nodes(params, args.offset, args.limit)
        print(json.dumps(nodes, indent=args.indent))
        return True


class cmd_count(NodeParamsCommand):  # pylint: disable=invalid-name
    """Count nodes with arbitrary parameters"""
    opt_args = None

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        params = self._split_params(args.params)
        count = api.count_nodes(params)
        print(count)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("node", globals(), args)
