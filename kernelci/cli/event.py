# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to interact with the Pub/Sub interface and message queues"""

import json

import click

from . import (
    Args,
    catch_error,
    echo_json,
    get_api,
    get_api_helper,
    kci,
)


@kci.group(name='event')
def kci_event():
    """Interact with Pub/Sub and message queue events"""


@kci_event.command(secrets=True)
@click.argument('channel')
@Args.config
@Args.api
@catch_error
def subscribe(config, api, channel, secrets):
    """Subscribe to a Pub/Sub channel"""
    api = get_api(config, api, secrets)
    sub_id = api.subscribe(channel)
    click.echo(sub_id)


@kci_event.command(secrets=True)
@click.argument('sub_id')
@Args.config
@Args.api
@catch_error
def unsubscribe(config, api, sub_id, secrets):
    """Unsubscribe from a Pub/Sub channel"""
    api = get_api(config, api, secrets)
    api.unsubscribe(sub_id)


@kci_event.command(secrets=True)
@click.argument('input_file', type=click.File('r'))
@click.argument('channel')
@click.option('--is-json', help="Parse input data as JSON", is_flag=True)
@Args.config
@Args.api
@catch_error
# pylint: disable=too-many-arguments
def send(input_file, channel, is_json, config, api, secrets):
    """Read some data and send it as an event on a channel"""
    api = get_api(config, api, secrets)
    data = json.load(input_file) if is_json else input_file.read()
    api.send_event(channel, {'data': data})


@kci_event.command(secrets=True)
@click.argument('sub_id')
@Args.config
@Args.api
@Args.indent
@catch_error
def receive(sub_id, config, api, indent, secrets):
    """Wait and receive an event from a subscription and print on stdout"""
    helper = get_api_helper(config, api, secrets)
    event = helper.receive_event_data(sub_id)
    if isinstance(event, str):
        click.echo(event.strip())
    elif isinstance(event, dict):
        echo_json(event, indent)
    else:
        click.echo(event)


@kci_event.command(secrets=True)
@click.argument('input_file', type=click.File('r'))
@click.argument('list_name')
@click.option('--is-json', help="Parse input data as JSON", is_flag=True)
@Args.config
@Args.api
@catch_error
# pylint: disable=too-many-arguments
def push(input_file, list_name, is_json, config, api, secrets):
    """Read some data and push it as an event on a list"""
    api = get_api(config, api, secrets)
    data = json.load(input_file) if is_json else input_file.read()
    api.push_event(list_name, {'data': data})


@kci_event.command(secrets=True)
@click.argument('list_name')
@Args.config
@Args.api
@Args.indent
@catch_error
def pop(list_name, config, api, indent, secrets):
    """Wait and pop an event from a List when received print on stdout"""
    helper = get_api_helper(config, api, secrets)
    event = helper.pop_event_data(list_name)
    if isinstance(event, str):
        click.echo(event.strip())
    elif isinstance(event, dict):
        echo_json(event, indent)
    else:
        click.echo(event)


@kci_event.command(secrets=True)
@Args.config
@Args.api
@Args.indent
@catch_error
def stats(config, api, indent, secrets):
    """Get Pub/Sub subscribers statistics (admin only)"""
    api = get_api(config, api, secrets)
    echo_json(api.subscription_stats(), indent)
