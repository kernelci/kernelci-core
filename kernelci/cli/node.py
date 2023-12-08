# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API node objects"""

import json

import click

from . import (
    Args,
    echo_json,
    get_api,
    get_pagination,
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
@Args.config
@Args.api
@Args.indent
@Args.page_length
@Args.page_number
# pylint: disable=too-many-arguments
def find(attributes, config, api, indent, page_length, page_number):
    """Find nodes with arbitrary attributes"""
    api = get_api(config, api)
    offset, limit = get_pagination(page_length, page_number)
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
@click.argument('input_file', type=click.File('r'))
@Args.config
@Args.api
@Args.indent
def submit(input_file, config, api, indent, secrets):
    """Submit a new node or update an existing one"""
    api = get_api(config, api, secrets)
    data = json.load(input_file)
    if 'id' in data:
        node = api.update_node(data)
    else:
        node = api.create_node(data)
    echo_json(node, indent)
