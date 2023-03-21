# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to show results and things from the API"""

from datetime import datetime

from .base import APICommand, Args, sub_main


class cmd_results(APICommand):  # pylint: disable=invalid-name
    """Show all the results for a given node"""

    COLORS = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'clear': '\033[0m',
    }

    COLOR_RESULT = {
        'pass': 'green',
        'fail': 'red',
        '----': 'yellow',
    }

    args = APICommand.args + [Args.id]

    def _color(self, msg, color):
        return ''.join([self.COLORS[color], msg, self.COLORS['clear']])

    def _print_color(self, msg, color):
        print(self._color(msg, color))

    @classmethod
    def _get_checkout(cls, api, node):
        while node['name'] != 'checkout':
            node = api.get_node(node['parent'])
        return node

    def _dump_results(self, api, node, indent=0):
        fmt = f"{{space}}{{path:{64-indent*2}s}}{{result:6}}{{node_id}}"
        node_id = node['_id']
        result = node['result'] or '----'
        line = fmt.format(
            space='  '*indent,
            path='.'.join(node['path']),
            result=result,
            node_id=node_id,
        )
        color = self.COLOR_RESULT.get(result)
        if color:
            line = self._color(line, color)
        print(line)
        child_nodes = api.get_nodes({'parent': node_id})
        for child in child_nodes:
            self._dump_results(api, child, indent+1)

    def _dump(self, api, args):
        node = api.get_node(args.id)
        parent_id = node['parent'] or '----'
        checkout = self._get_checkout(api, node)
        revision = node['revision']
        created = datetime.fromisoformat(node['created'])
        print(f"""\
{self._color('Node', 'bold')}
  {self._color('path', 'blue')}      {'.'.join(node['path'])}
  {self._color('id', 'blue')}        {args.id}
  {self._color('parent', 'blue')}    {parent_id}
  {self._color('created', 'blue')}   {created.strftime('%Y-%m-%d at %H:%M:%S')}

{self._color('Kernel', 'bold')}
  {self._color('tree', 'blue')}      {revision['tree']}
  {self._color('branch', 'blue')}    {revision['branch']}
  {self._color('commit', 'blue')}    {revision['commit']}
  {self._color('describe', 'blue')}  {revision['describe']}
  {self._color('tarball', 'blue')}   {checkout['artifacts'].get('tarball')}

{self._color('Results', 'bold')}""")
        self._dump_results(api, node)

    def _api_call(self, api, configs, args):
        self._dump(api, args)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("show", globals(), args)
