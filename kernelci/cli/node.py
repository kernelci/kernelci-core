# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
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
            'help': "Indentation string in JSON output",
        },
    ]

    @classmethod
    def _get_api(cls, configs, args):
        config = configs['api_configs'][args.api_config]
        return kernelci_api.KernelCI_API(config, args.api_token)

    def __call__(self, configs, args):
        pass


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


class cmd_find(NodeCommand):  # pylint: disable=invalid-name
    """Find nodes with arbitrary parameters"""
    args = NodeCommand.args + [
        {
            'name': 'params',
            'nargs': '+',
            'help': "Parameters to find nodes in param=value format",
        },
    ]
    opt_args = NodeCommand.opt_args + [
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
        params = dict(
            tuple(param.split('=')) for param in args.params
        )
        nodes = api.get_nodes(params, args.offset, args.limit)
        print(json.dumps(nodes, indent=args.indent))
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("node", globals(), args)
