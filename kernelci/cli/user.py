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

from . import (
    Args,
    catch_error,
    echo_json,
    get_api,
    kci,
    split_attributes,
)


@kci.group(name='user')
def kci_user():
    """Manage user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
@catch_error
def whoami(config, api, indent, secrets):
    """Get the current user's details with API authentication"""
    api = get_api(config, api, secrets)
    data = api.user.whoami()
    echo_json(data, indent)


@kci_user.command(secrets=True)
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
@Args.indent
@catch_error
def find(attributes, config, api, indent, secrets):
    """Find user profiles with arbitrary attributes"""
    api = get_api(config, api, secrets)
    attributes = split_attributes(attributes)
    users = api.user.find(attributes)
    data = json.dumps(users, indent=indent or None)
    echo = click.echo_via_pager if len(users) > 1 else click.echo
    echo(data)


@kci_user.command
@click.argument('username')
@Args.config
@Args.api
@catch_error
def token(username, config, api):
    """Create a new API token using a user name and password"""
    api = get_api(config, api)
    password = getpass.getpass()
    api_token = api.user.create_token(username, password)
    click.echo(api_token['access_token'])


@kci_user.command(secrets=True)
@click.argument('attributes', nargs=-1)
@click.option('--username', help="Username of the user to update (admin only)")
@Args.config
@Args.api
@catch_error
def update(attributes, username, config, api, secrets):
    """Update user account data with the provided attributes"""
    fields = split_attributes(attributes)
    if not fields:
        click.echo("No user details to update.")
        return

    api = get_api(config, api, secrets)
    if username:
        users = api.user.find({"username": username})
        if not users:
            raise click.ClickException(f"User not found: {username}")
        user_id = users[0]['id']
    else:
        user_id = None
    api.user.update(fields, user_id)


@kci_user.command(secrets=True)
@click.argument('username')
@click.argument('email')
@Args.config
@Args.api
@catch_error
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
    api = get_api(config, api, secrets)
    api.user.add(user)


@kci_user.command
@click.argument('email')
@Args.config
@Args.api
@catch_error
def verify(email, config, api):
    """Verify the user's email address"""
    api = get_api(config, api)
    click.echo(f"Sending verification token to {email}")
    api.user.request_verification_token(email)
    verification_token = click.prompt("Verification token")
    api.user.verify_email(verification_token)
    click.echo("Email verification successful!")


@kci_user.command(secrets=True)
@click.argument('user_id')
@Args.config
@Args.api
@Args.indent
@catch_error
def get(user_id, config, api, indent, secrets):
    """Get a user with a given ID"""
    api = get_api(config, api, secrets)
    user = api.user.get(user_id)
    echo_json(user, indent)


@kci_user.command(secrets=True)
@click.argument('username')
@Args.config
@Args.api
@catch_error
def activate(username, config, api, secrets):
    """Activate user account (admin only)"""
    api = get_api(config, api, secrets)
    users = api.user.find({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    api.user.update({"is_active": 1}, user['id'])


@kci_user.command(secrets=True)
@click.argument('username')
@Args.config
@Args.api
@catch_error
def deactivate(username, config, api, secrets):
    """Deactivate a user account (admin only)"""
    api = get_api(config, api, secrets)
    users = api.user.find({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    api.user.update({"is_active": 0}, user['id'])


@kci_user.group(name='password')
def user_password():
    """Manage user passwords"""


@user_password.command(name='update')
@click.argument('username')
@Args.config
@Args.api
@catch_error
def password_update(username, config, api):
    """Update password for a user account"""
    api = get_api(config, api)
    current_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if new_password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    api.user.update_password(username, current_password, new_password)


@user_password.command(name='reset')
@click.argument('email')
@Args.config
@Args.api
@catch_error
def password_reset(email, config, api):
    """Reset password for a user account"""
    api = get_api(config, api)
    click.echo(f"Sending reset token to {email}")
    api.user.request_password_reset_token(email)
    reset_token = click.prompt("Reset token")
    password = getpass.getpass("New password: ")
    retyped = getpass.getpass("Retype new password: ")
    if password != retyped:
        raise click.ClickException("Sorry, passwords do not match")
    api.user.reset_password(reset_token, password)


@kci_user.group(name='group')
def user_group():
    """Manage user groups"""


@user_group.command(name='find')
@click.argument('attributes', nargs=-1)
@Args.config
@Args.api
@Args.indent
@catch_error
def find_groups(attributes, config, api, indent):
    """Find user groups with arbitrary attributes"""
    api = get_api(config, api)
    attributes = split_attributes(attributes)
    users = api.get_groups(attributes)
    data = json.dumps(users, indent=indent or None)
    echo = click.echo_via_pager if len(users) > 1 else click.echo
    echo(data)


@user_group.command(name="add", secrets=True)
@click.argument('name')
@Args.config
@Args.api
@catch_error
def group_add(name, config, api, secrets):
    """Create a new group"""
    api = get_api(config, api, secrets)
    api.create_group(name)


@user_group.command(secrets=True)
@click.argument('name')
@click.option('--username', required=True)
@Args.config
@Args.api
@catch_error
def join(name, username, config, api, secrets):
    """Add a user to a group (admin only)"""
    api = get_api(config, api, secrets)
    users = api.user.find({"username": username})
    if not users:
        raise click.ClickException(f"User not found: {username}")
    user = users[0]
    groups = [name]
    for group in users[0]['groups']:
        groups.append(group['name'])
    api.user.update({"groups": groups}, user['id'])


@user_group.command(secrets=True)
@click.argument('name')
@Args.config
@Args.api
@catch_error
def leave(name, config, api, secrets):
    """Leave a user group"""
    api = get_api(config, api, secrets)
    user = api.user.whoami()
    groups = []
    for group in user['groups']:
        groups.append(group['name'])
    if name in groups:
        groups.remove(name)
        api.user.update({"groups": groups}, None)


@user_group.command(secrets=True)
@click.argument('name')
@Args.config
@Args.api
@catch_error
def delete(name, config, api, secrets):
    """Delete a user group (admin only)"""
    api = get_api(config, api, secrets)
    groups = api.get_groups({"name": name})
    if not groups:
        raise click.ClickException(f"Group not found: {name}")
    api.delete_group(groups[0]['id'])
