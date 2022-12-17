# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
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


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("node", globals(), args)
