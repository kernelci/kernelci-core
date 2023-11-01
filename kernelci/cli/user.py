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


@user_password.command
@click.argument('username')
@Args.config
@Args.api
def update(username, config, api):
    """Update the password for a given user"""
    current = getpass.getpass("Current password: ")
    new = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if new != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    api.change_password(username, current, new)


@kci_user.command(secrets=True)
@click.argument('username')
@click.argument('email')
@Args.config
@Args.api
def add(username, email, config, api, secrets):
    """Add a new user account"""
    profile = {
        'email': email,
    }
    password = getpass.getpass()
    retyped = getpass.getpass("Confirm password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    api.create_user(username, password, profile)
