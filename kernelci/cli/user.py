# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API users"""

import getpass

from .base import Args, sub_main
from .base_api import APICommand, AttributesCommand


class cmd_whoami(APICommand):  # pylint: disable=invalid-name
    """Use the /whoami entry point to get the current user's data"""
    args = APICommand.args + [Args.api_token]
    opt_args = APICommand.opt_args + [Args.indent]

    def _api_call(self, api, configs, args):
        data = api.whoami()
        self._print_json(data, args.indent)
        return True


class cmd_get_token(APICommand):  # pylint: disable=invalid-name
    """Create a new API token for the current user"""
    args = APICommand.args + [Args.username]
    opt_args = APICommand.opt_args + [
        {
            'name': '--scopes',
            'action': 'append',
            'help': "Security scopes",
        },
    ]

    def _api_call(self, api, configs, args):
        password = getpass.getpass()
        token = api.create_token(args.username, password, args.scopes)
        self._print_json(token, args.indent)
        return True


class cmd_password_hash(APICommand):  # pylint: disable=invalid-name
    """Get an encryption hash for an arbitrary password"""

    def _api_call(self, api, configs, args):
        password = getpass.getpass()
        print(api.password_hash(password))
        return True


class cmd_change_password(APICommand):  # pylint: disable=invalid-name
    """Change a password for a given user"""
    args = APICommand.args + [Args.username]

    def _api_call(self, api, configs, args):
        current = getpass.getpass("Current password: ")
        new = getpass.getpass("New password: ")
        retyped = getpass.getpass("Retype new password: ")
        if new != retyped:
            print("Sorry, passwords do not match.")
            return False
        api.change_password(args.username, current, new)
        return True


class cmd_get_group(APICommand):  # pylint: disable=invalid-name
    """Get a user group with a given ID"""
    args = APICommand.args + [Args.group_id]
    opt_args = APICommand.opt_args + [Args.indent]

    def _api_call(self, api, configs, args):
        group = api.get_group(args.group_id)
        self._print_json(group, args.indent)
        return True


class cmd_find_groups(AttributesCommand):  # pylint: disable=invalid-name
    """Find user groups with arbitrary attributes"""
    opt_args = AttributesCommand.opt_args + [
        Args.limit, Args.offset
    ]

    def _api_call(self, api, configs, args):
        attributes = self._split_attributes(args.attributes)
        groups = api.get_groups(attributes, args.offset, args.limit)
        self._print_json(groups, args.indent)
        return True


class cmd_add(APICommand):  # pylint: disable=invalid-name
    """Add a new user account"""
    args = APICommand.args + [
        Args.api_token,
        {
            'name': 'username',
            'help': "Username of the new user",
        },
        {
            'name': 'email',
            'help': "Email address of the new user",
        },
    ]

    def _api_call(self, api, configs, args):
        profile = {
            'email': args.email,
        }
        password = getpass.getpass()
        api.create_user(args.username, password, profile)
        return True


class cmd_find_users(AttributesCommand):  # pylint: disable=invalid-name
    """Find user profiles with arbitrary attributes"""
    opt_args = AttributesCommand.opt_args + [
       Args.limit, Args.offset
    ]

    def _api_call(self, api, configs, args):
        attributes = self._split_attributes(args.attributes)
        profiles = api.get_user_profiles(attributes, args.offset, args.limit)
        self._print_json(profiles, args.indent)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("user", globals(), args)
