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
    catch_error,
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
@catch_error
def get(node_id, config, api, indent):
    """Get a node with a given ID"""
    api = get_api(config, api)
    node = api.node.get(node_id)
    echo_json(node, indent)


@kci_node.command
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
@Args.indent
@Args.page_length
@Args.page_number
@catch_error
# pylint: disable=too-many-arguments
def find(attributes, config, api, indent, page_length, page_number):
    """Find nodes with arbitrary attributes"""
    api = get_api(config, api)
    offset, limit = get_pagination(page_length, page_number)
    attributes = split_attributes(attributes)
    nodes = api.node.find(attributes, offset, limit)
    data = json.dumps(nodes, indent=indent or None)
    echo = click.echo_via_pager if len(nodes) > 1 else click.echo
    echo(data)


@kci_node.command
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
@catch_error
def count(attributes, config, api):
    """Count nodes with arbitrary attributes"""
    api = get_api(config, api)
    attributes = split_attributes(attributes)
    result = api.node.count(attributes)
    click.echo(result)


@kci_node.command(secrets=True)
@click.argument('input_file', type=click.File('r'))
@Args.config
@Args.api
@Args.indent
@catch_error
def submit(input_file, config, api, indent, secrets):
    """Submit a new node or update an existing one"""
    api = get_api(config, api, secrets)
    data = json.load(input_file)
    func = api.node.update if 'id' in data else api.node.add
    node = func(data)
    echo_json(node, indent)
