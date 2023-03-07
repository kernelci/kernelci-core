# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to interact with the KernelCI API"""

from .base import APICommand, Args, sub_main


class cmd_hello(APICommand):  # pylint: disable=invalid-name
    """Get the hello message"""

    opt_args = APICommand.opt_args + [Args.indent]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        hello = api.hello()
        self._print_json(hello, args.indent)
        return True


class cmd_version(APICommand):  # pylint: disable=invalid-name
    """Get the API version"""

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        print(api.version)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("api", globals(), args)
