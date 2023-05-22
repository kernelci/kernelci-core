# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to interact with the Pub/Sub interface"""

import json
import sys

import kernelci

from .base import Args, sub_main
from .base_api import APICommand


class cmd_subscribe(APICommand):  # pylint: disable=invalid-name
    """Subscribe to a Pub/Sub channel"""
    args = APICommand.args + [Args.api_token, Args.channel]

    def _api_call(self, api, configs, args):
        sub_id = api.subscribe(args.channel)
        print(sub_id)
        return True


class cmd_unsubscribe(APICommand):  # pylint: disable=invalid-name
    """Unscribe from a Pub/Sub channel"""
    args = APICommand.args + [Args.api_token, Args.sub_id]

    def _api_call(self, api, configs, args):
        api.unsubscribe(args.sub_id)
        return True


class cmd_send_event(APICommand):  # pylint: disable=invalid-name
    """Read some data on stdin and send it as an event on a channel"""
    args = APICommand.args + [Args.api_token, Args.channel]
    opt_args = [
        {
            'name': '--type',
            'help': "CloudEvent type, api.kernelci.org by default",
        },
        {
            'name': '--source',
            'help': "CloudEvent source, https://api.kernelci.org/ by default",
        },
        {
            'name': '--json',
            'action': 'store_true',
            'help': "Parse input data as JSON",
        },
    ]

    def _api_call(self, api, configs, args):
        data = sys.stdin.read()
        if args.json:
            data = json.loads(data)
        api.send_event(args.channel, {'data': data})
        return True


class cmd_receive_event(APICommand):  # pylint: disable=invalid-name
    """Wait and receive an event from a subscription and print on stdout"""
    args = APICommand.args + [Args.api_token, Args.sub_id]
    opt_args = APICommand.opt_args + [Args.indent]

    def _api_call(self, api, configs, args):
        helper = kernelci.api.helper.APIHelper(api)
        event = helper.receive_event_data(args.sub_id)
        if isinstance(event, str):
            print(event.strip())
        elif isinstance(event, dict):
            self._print_json(event, args.indent)
        else:
            print(event)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("pubsub", globals(), args)
