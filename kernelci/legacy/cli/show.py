# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to show results and things from the API"""

from datetime import datetime

from .base import Args, sub_main
from .base_api import APICommand


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
    opt_args = APICommand.opt_args + [
        {
            'name': '--max-depth',
            'type': int,
            'help': "Maximum depth when recursing through child results",
        },
    ]

    def _color(self, msg, color):
        return ''.join([self.COLORS[color], msg, self.COLORS['clear']])

    def _print_color(self, msg, color):
        print(self._color(msg, color))

    @classmethod
    def _get_checkout(cls, api, node):
        while node['name'] != 'checkout':
            node = api.get_node(node['parent'])
        return node

    def _dump_artifacts(self, artifacts):
        for name, url in artifacts.items():
            print(f"  {self._color(name, 'blue')}")
            print(f"    {url}")

    def _dump_data(self, data):
        max_len = max(len(key) for key in data)
        width = max(max_len, 9) + 9
        fmt = f"  {{key:{width}s}} {{value}}"
        for key, value in data.items():
            print(fmt.format(key=self._color(key, 'blue'), value=value))

    def _dump_results(self, api, node, indent=0, max_depth=0):
        fmt = f"{{name:{64-indent*2}s}}{{result:6}}{{node_id}}"
        name = node['name']
        result = node['result'] or '----'
        node_id = node['id']
        line = fmt.format(
            name=name,
            result=result,
            node_id=node_id,
        )
        color = self.COLOR_RESULT.get(result)
        if color:
            line = self._color(line, color)
        if name == node['group']:
            line = self._color(line, 'underline')
        print('  '*indent, end='')
        print(line)
        if max_depth and indent == max_depth:
            return
        child_nodes = api.get_nodes({'parent': node_id})
        for child in child_nodes:
            self._dump_results(api, child, indent+1, max_depth)

    def _dump(self, api, args):
        node = api.get_node(args.id)
        if node is None:
            print(f"Node not found: {args.id}")
            return False

        parent_id = node['parent'] or '----'
        revision = node['revision']
        owner = node['owner']
        created = datetime.fromisoformat(node['created'])
        artifacts = node.get('artifacts')
        data = node.get('data')

        print(f"""\
{self._color('Node', 'bold')}
  {self._color('path', 'blue')}      {'.'.join(node['path'])}
  {self._color('id', 'blue')}        {args.id}
  {self._color('parent', 'blue')}    {parent_id}
  {self._color('owner', 'blue')}     {owner}
  {self._color('created', 'blue')}   {created.strftime('%Y-%m-%d at %H:%M:%S')}
  {self._color('state', 'blue')}     {node['state']}

{self._color('Kernel', 'bold')}
  {self._color('tree', 'blue')}      {revision['tree']}
  {self._color('branch', 'blue')}    {revision['branch']}
  {self._color('commit', 'blue')}    {revision['commit']}
  {self._color('describe', 'blue')}  {revision['describe']}
""")

        if artifacts:
            print(f"{self._color('Artifacts', 'bold')}")
            self._dump_artifacts(artifacts)
            print()

        if data:
            print(f"{self._color('Data', 'bold')}")
            self._dump_data(data)
            print()

        print(f"{self._color('Results', 'bold')}")
        self._dump_results(api, node, 0, args.max_depth)

        return True

    def _api_call(self, api, configs, args):
        return self._dump(api, args)


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("show", globals(), args)
