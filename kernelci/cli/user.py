# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API users"""

import getpass

from .base import Args, APICommand, sub_main


class cmd_whoami(APICommand):  # pylint: disable=invalid-name
    """Use the /whoami entry point to get the current user's data"""
    args = APICommand.args + [Args.api_token]
    opt_args = APICommand.opt_args + [Args.indent]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
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

    def __call__(self, configs, args):
        password = getpass.getpass()
        api = self._get_api(configs, args)
        token = api.create_token(args.username, password, args.scopes)
        self._print_json(token, args.indent)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("user", globals(), args)
