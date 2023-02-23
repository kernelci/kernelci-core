# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage KernelCI API users"""

import json

from kernelci.db import kernelci_api
from .base import Args, Command, sub_main


class cmd_me(Command):  # pylint: disable=invalid-name
    """Use the /me entry point to get the current user's data"""
    args = [
        Args.api_config, Args.api_token,
    ]
    opt_args = [
        {
            'name': '--indent',
            'help': "Indentation string in JSON output",
        },
    ]

    @classmethod
    def _get_api(cls, configs, args):
        config = configs['api_configs'][args.api_config]
        return kernelci_api.KernelCI_API(config, args.api_token)

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        data = api.me()
        print(json.dumps(data, indent=args.indent))
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("user", globals(), args)
