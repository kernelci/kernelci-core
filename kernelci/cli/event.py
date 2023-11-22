# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to interact with the Pub/Sub interface and message queues"""

import sys
import json

import click

import kernelci.api
import kernelci.api.helper
import kernelci.config
from . import Args, kci


@kci.group(name='event')
def kci_event():
    """Interact with Pub/Sub and message queue events"""


@kci_event.command(secrets=True)
@click.argument('channel')
@Args.config
@Args.api
def subscribe(config, api, channel, secrets):
    """Subscribe to a Pub/Sub channel"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    sub_id = api.subscribe(channel)
    click.echo(sub_id)


@kci_event.command(secrets=True)
@click.argument('sub_id')
@Args.config
@Args.api
def unsubscribe(config, api, sub_id, secrets):
    """Unsubscribe from a Pub/Sub channel"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    api.unsubscribe(sub_id)


@kci_event.command(secrets=True)
@click.option('--is-json', help="Parse input data as JSON", is_flag=True)
@Args.config
@Args.api
@click.argument('channel')
def send(config, api, is_json, channel, secrets):
    """Read some data on stdin and send it as an event on a channel"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = sys.stdin.read()
    if is_json:
        data = json.loads(data)
    api.send_event(channel, {'data': data})


@kci_event.command(secrets=True)
@click.argument('sub_id')
@Args.config
@Args.api
@Args.indent
def receive(config, api, indent, sub_id, secrets):
    """Wait and receive an event from a subscription and print on stdout"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    helper = kernelci.api.helper.APIHelper(api)
    event = helper.receive_event_data(sub_id)
    if isinstance(event, str):
        click.echo(event.strip())
    elif isinstance(event, dict):
        click.echo(json.dumps(event, indent=indent))
    else:
        click.echo(event)


@kci_event.command(secrets=True)
@click.option('--is-json', help="Parse input data as JSON", is_flag=True)
@Args.config
@Args.api
@click.argument('list_name')
def push(config, api, is_json, list_name, secrets):
    """Read some data on stdin and push it as an event on a list"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = sys.stdin.read()
    if is_json:
        data = json.loads(data)
    api.push_event(list_name, {'data': data})


@kci_event.command(secrets=True)
@click.argument('list_name')
@Args.config
@Args.api
@Args.indent
def pop(config, api, indent, list_name, secrets):
    """Wait and pop an event from a List when received print on stdout"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    helper = kernelci.api.helper.APIHelper(api)
    event = helper.pop_event_data(list_name)
    if isinstance(event, str):
        click.echo(event.strip())
    elif isinstance(event, dict):
        click.echo(json.dumps(event, indent=indent))
    else:
        click.echo(event)
