# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>
# Author: Paweł Wieczorek <pawiecz@collabora.com>

"""Tool to manage KernelCI API users"""

import getpass
import json

import click

import kernelci.api
import kernelci.config
from . import Args, kci, split_attributes


@kci.group(name='user')
def kci_user():
    """Manage user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
def whoami(config, api, indent, secrets):
    """Get the current user's details with API authentication"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.whoami()
    click.echo(json.dumps(data, indent=indent))


@kci_user.command
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
@Args.indent
def find(attributes, config, api, indent):
    """Find user profiles with arbitrary attributes"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    users = api.get_users(split_attributes(attributes))
    data = json.dumps(users, indent=indent)
    echo = click.echo_via_pager if len(users) > 1 else click.echo
    echo(data)


@kci_user.command
@click.argument('username')
@Args.config
@Args.api
@Args.indent
def token(username, config, api, indent):
    """Create a new API token using a user name and password"""
    password = getpass.getpass()
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    user_token = api.create_token(username, password)
    click.echo(json.dumps(user_token, indent=indent))


@kci_user.group(name='password')
def user_password():
    """Manage user passwords"""


@kci_user.command(secrets=True)
@click.option('--username')
@click.option('--email')
@click.option('--group', multiple=True, help="User group(s)")
@Args.config
@Args.api
@Args.indent
def update(username, email, config,  # pylint: disable=too-many-arguments
           api, secrets, group, indent):
    """Update own user account"""
    user = {}
    if username:
        user['username'] = username
    if email:
        user['email'] = email
    if group:
        user['groups'] = group
    if not user:
        raise click.ClickException("Sorry, nothing to update")
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.update_user(user)
    click.echo(json.dumps(data, indent=indent))


@kci_user.command(secrets=True)
@click.argument('username')
@click.argument('email')
@click.option('--group', multiple=True, help="User group(s)")
@Args.config
@Args.api
@Args.indent
def add(username, email, config,  # pylint: disable=too-many-arguments
        api, secrets, group, indent):
    """Add a new user account"""
    password = getpass.getpass()
    retyped = getpass.getpass("Confirm password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    user = {
        'username': username,
        'email': email,
        'password': password,
        'groups': group
    }
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.create_user(user)
    click.echo(json.dumps(data, indent=indent))