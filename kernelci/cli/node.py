# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API node objects"""

import json
import sys

import click

import kernelci.api
import kernelci.config
from . import Args, kci, split_attributes


@kci.group(name='node')
def kci_node():
    """Interact with Node objects"""


@kci_node.command
@click.argument('node_id')
@Args.config
@Args.api
@Args.indent
def get(node_id, config, api, indent):
    """Get a node with a given ID"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    node = api.get_node(node_id)
    click.echo(json.dumps(node, indent=indent))


@kci_node.command
@click.argument('attributes', nargs=-1)
@click.option('--offset', help="Offset for paginated results")
@click.option('--limit',
              help="Maximum number of results to retrieve."
              "When set to 0, no limit is used and all the "
              "matching results are retrieved.")
@Args.config
@Args.api
@Args.indent
def find(attributes, config, api,   # pylint: disable=too-many-arguments
         indent, offset, limit):
    """Find nodes with arbitrary attributes"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    nodes = api.get_nodes(split_attributes(attributes), offset, limit)
    data = json.dumps(nodes, indent=indent)
    echo = click.echo_via_pager if len(nodes) > 1 else click.echo
    echo(data)


@kci_node.command
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
def count(attributes, config, api):
    """Count nodes with arbitrary attributes"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    click.echo(api.count_nodes(split_attributes(attributes)))


@kci_node.command(secrets=True)
@Args.config
@Args.api
@Args.indent
def submit(config, api, secrets, indent):
    """Submit a new node or update an existing one from stdin"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = json.load(sys.stdin)
    if 'id' in data:
        node = api.update_node(data)
    else:
        node = api.create_node(data)
    click.echo(json.dumps(node, indent=indent))
