# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API node objects"""

import json
import sys

from .base import Args, sub_main
from .base_api import APICommand, AttributesCommand


class NodeCommand(APICommand):  # pylint: disable=too-few-public-methods
    """Base command class for interacting with Node objects"""
    opt_args = APICommand.opt_args + [Args.indent]


class cmd_get(NodeCommand):  # pylint: disable=invalid-name
    """Get a node with a given ID"""
    args = NodeCommand.args + [Args.id]

    def _api_call(self, api, configs, args):
        node = api.get_node(args.id)
        self._print_json(node, args.indent)
        return True


class cmd_find(AttributesCommand):  # pylint: disable=invalid-name
    """Find nodes with arbitrary attributes"""
    opt_args = AttributesCommand.opt_args + [
        {
            'name': '--limit',
            'type': int,
            'help': """\
Maximum number of nodes to retrieve. When set to 0, no limit is used and all
the matching nodes are retrieved.\
""",
            'default': 10,
        },
        {
            'name': '--offset',
            'type': int,
            'help': "Offset when paginating results with a number of nodes",
        },
    ]

    def _api_call(self, api, configs, args):
        attributes = self._split_attributes(args.attributes)
        nodes = api.get_nodes(attributes, args.offset, args.limit)
        self._print_json(nodes, args.indent)
        return True


class cmd_count(AttributesCommand):  # pylint: disable=invalid-name
    """Count nodes with arbitrary attributes"""

    def _api_call(self, api, configs, args):
        attributes = self._split_attributes(args.attributes)
        count = api.count_nodes(attributes)
        print(count)
        return True


class cmd_submit(APICommand):  # pylint: disable=invalid-name
    """Submit a new node or update an existing one from stdin"""
    args = APICommand.args + [Args.api_token]
    opt_args = APICommand.opt_args + [Args.id_only]

    def _api_call(self, api, configs, args):
        data = json.load(sys.stdin)
        if 'id' in data:
            node = api.update_node(data)
        else:
            node = api.create_node(data)
        self._print_node(node, args.id_only, args.indent)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("node", globals(), args)
