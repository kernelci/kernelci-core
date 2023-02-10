# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API users"""

import json

from .base import APICommand, sub_main


class cmd_me(APICommand):  # pylint: disable=invalid-name
    """Use the /me entry point to get the current user's data"""
    opt_args = [
        {
            'name': '--indent',
            'help': "Indentation string in JSON output",
        },
    ]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        data = api.me()
        print(json.dumps(data, indent=args.indent))
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("user", globals(), args)
