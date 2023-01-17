# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API node objects"""

from kernelci.db import kernelci_api
from .base import Args, Command, sub_main


class cmd_get(Command):  # pylint: disable=invalid-name
    """Get a node with a given ID"""
    args = [
        Args.api_config, Args.api_token,
        {
            'name': 'id',
            'help': "Node id",
        },
    ]

    def __call__(self, configs, args):
        config = configs['api_configs'][args.api_config]
        api = kernelci_api.KernelCI_API(config, args.api_token)
        node = api.get_node(args.id)
        print(node)
        return True


class cmd_find(Command):  # pylint: disable=invalid-name
    """Find nodes with arbitrary parameters"""
    args = [
        Args.api_config, Args.api_token,
        {
            'name': 'params',
            'nargs': '+',
            'help': "Parameters to find nodes in param=value format",
        },
    ]
    opt_args = [
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
        config = configs['api_configs'][args.api_config]
        api = kernelci_api.KernelCI_API(config, args.api_token)
        params = dict(
            tuple(param.split('=')) for param in args.params
        )
        nodes = api.get_nodes(params, args.offset, args.limit)
        print(nodes)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("node", globals(), args)
