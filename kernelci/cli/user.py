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


@kci_user.command
@click.argument('email')
@Args.config
@Args.api
def verify(email, config, api):
    """Email verification for a user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    api.request_verification_token(email)
    verification_token = input(
        "Please enter the token we sent to you via email:")
    res = api.verify_user(verification_token)
    if res.status_code == 200:
        click.echo("Email verification successful!")


@user_password.command
@click.argument('email')
@Args.config
@Args.api
def reset(email, config, api):
    """Reset password for a user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    api.request_password_reset_token(email)
    reset_token = input("Please enter the token we sent to you via email:")
    password = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    res = api.reset_password(reset_token, password)
    if res.status_code == 200:
        click.echo("Password reset successful!")


@kci_user.command
@click.argument('user_id')
@Args.config
@Args.api
@Args.indent
def get(user_id, config, api, indent):
    """Get a user with a given ID"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    data = api.get_user(user_id)
    click.echo(json.dumps(data, indent=indent))


@kci_user.command(secrets=True)
@click.argument('username')
@click.option('--email')
@click.option('--group', multiple=True, help="User group(s)")
@Args.config
@Args.api
@Args.indent
def update_by_username(username, email,  # pylint: disable=too-many-arguments
                       config, api, secrets, group, indent):
    """[Scope: admin] Update user account matching given username"""
    user = {}
    if email:
        user['email'] = email
    if group:
        user['groups'] = group
    if not user:
        raise click.ClickException("Sorry, nothing to update")
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    users = api.get_users({"username": username})
    if not users:
        raise click.ClickException(
            "Sorry, user does not exist with given username")
    user_id = users[0]["id"]
    data = api.update_user(user, user_id)
    click.echo(json.dumps(data, indent=indent))


@kci_user.command(secrets=True)
@click.argument('user_id')
@Args.config
@Args.api
@Args.indent
def activate(user_id, config, api, secrets, indent):
    """[Scope: admin] Activate user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.update_user({"is_active": 1}, user_id)
    click.echo(json.dumps(data, indent=indent))


@kci_user.command(secrets=True)
@click.argument('user_id')
@Args.config
@Args.api
@Args.indent
def deactivate(user_id, config, api, secrets, indent):
    """[Scope: admin] Deactivate a user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.update_user({"is_active": 0}, user_id)
    click.echo(json.dumps(data, indent=indent))


@user_password.command(name='update')
@click.argument('username')
@Args.config
@Args.api
def password_update(username, config, api):
    """Update password for a user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    current_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if new_password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    res = api.update_password(username, current_password, new_password)
    if res.status_code == 200:
        click.echo("Password update successful!")
