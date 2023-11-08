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
from . import Args, kci, split_attributes, catch_http_error


@kci.group(name='user')
def kci_user():
    """Manage user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
@catch_http_error
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
@catch_http_error
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
@catch_http_error
def token(username, config, api):
    """Create a new API token using a user name and password"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    password = getpass.getpass()
    api_token = api.create_token(username, password)
    click.echo(api_token['access_token'])


@kci_user.command(secrets=True)
@click.argument('attributes', nargs=-1)
@click.option('--username', help="Username of the user to update (admin only)")
@Args.config
@Args.api
@catch_http_error
def update(attributes, username, config, api, secrets):
    """Update user account data with the provided attributes"""
    fields = split_attributes(attributes)
    if not fields:
        click.echo("No user details to update.")
        return

    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    if username:
        users = api.get_users({"username": username})
        if not users:
            raise click.ClickException(f"User not found: {username}")
        user_id = users[0]['id']
    else:
        user_id = None
    api.update_user(fields, user_id)


@kci_user.command(secrets=True)
@click.argument('username')
@click.argument('email')
@Args.config
@Args.api
@catch_http_error
def add(username, email, config, api, secrets):
    """Add a new user account"""
    password = getpass.getpass()
    retyped = getpass.getpass("Confirm password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    user = {
        'username': username,
        'email': email,
        'password': password,
    }
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    api.create_user(user)


@kci_user.command
@click.argument('username')
@Args.config
@Args.api
@catch_http_error
def verify(username, config, api):
    """Verify the user's email address"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    users = api.get_users({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    email = user['email']
    click.echo(f"Sending verification token to {email}")
    api.request_verification_token(email)
    verification_token = click.prompt("Verification token")
    api.verify_user(verification_token)
    click.echo("Email verification successful!")


@kci_user.command
@click.argument('user_id')
@Args.config
@Args.api
@Args.indent
@catch_http_error
def get(user_id, config, api, indent):
    """Get a user with a given ID"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    user = api.get_user(user_id)
    click.echo(json.dumps(user, indent=indent))


@kci_user.command(secrets=True)
@click.argument('username')
@Args.config
@Args.api
@catch_http_error
def activate(username, config, api, secrets):
    """Activate user account (admin only)"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    users = api.get_users({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    api.update_user({"is_active": 1}, user['id'])


@kci_user.command(secrets=True)
@click.argument('username')
@Args.config
@Args.api
@catch_http_error
def deactivate(username, config, api, secrets):
    """Deactivate a user account (admin only)"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    users = api.get_users({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    api.update_user({"is_active": 0}, user['id'])


@kci_user.group(name='password')
def user_password():
    """Manage user passwords"""


@user_password.command(name='update')
@click.argument('username')
@Args.config
@Args.api
@catch_http_error
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
    api.update_password(username, current_password, new_password)


@user_password.command(name='reset')
@click.argument('username')
@Args.config
@Args.api
@catch_http_error
def password_reset(username, config, api):
    """Reset password for a user account"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    users = api.get_users({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    email = user['email']
    click.echo(f"Sending reset token to {email}")
    api.request_password_reset_token(email)
    reset_token = click.prompt("Reset token")
    password = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    api.reset_password(reset_token, password)
