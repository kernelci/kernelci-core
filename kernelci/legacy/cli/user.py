# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API users"""

from .base import Args, sub_main
from .base_api import APICommand, AttributesCommand


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


class cmd_update(APICommand):  # pylint: disable=invalid-name
    """Update a new user account"""
    args = APICommand.args + [
        Args.api_token,
        {
            'name': 'username',
            'help': "Username of the user",
        },
    ]
    opt_args = [
        Args.indent,
        {
            'name': '--email',
            'help': "New email address of the user",
        },
        {
            'name': '--groups',
            'nargs': '*',
            'help': "User group",
        }
    ]

    def _api_call(self, api, configs, args):
        profile = {
            'email': args.email,
            'groups': args.groups,
        }
        response = api.update_user(args.username, profile)
        self._print_json(response.json(), args.indent)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("user", globals(), args)
