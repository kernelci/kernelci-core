# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API node objects"""

import json
import sys

import click

from . import (
    Args,
    echo_json,
    get_api,
    kci,
    split_attributes,
)


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
    api = get_api(config, api)
    node = api.get_node(node_id)
    echo_json(node, indent)


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
    api = get_api(config, api)
    attributes = split_attributes(attributes)
    nodes = api.get_nodes(attributes, offset, limit)
    data = json.dumps(nodes, indent=indent or None)
    echo = click.echo_via_pager if len(nodes) > 1 else click.echo
    echo(data)


@kci_node.command
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
def count(attributes, config, api):
    """Count nodes with arbitrary attributes"""
    api = get_api(config, api)
    attributes = split_attributes(attributes)
    click.echo(api.count_nodes(attributes))


@kci_node.command(secrets=True)
@Args.config
@Args.api
@Args.indent
def submit(config, api, secrets, indent):
    """Submit a new node or update an existing one from stdin"""
    api = get_api(config, api, secrets)
    data = json.load(sys.stdin)
    if 'id' in data:
        node = api.update_node(data)
    else:
        node = api.create_node(data)
    echo_json(node, indent)
