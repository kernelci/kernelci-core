# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to use the KernelCI scheduler"""

import json
import sys

import kernelci.runtime
import kernelci.scheduler
from .base import Args, Command, sub_main


class cmd_get_schedule(Command):  # pylint: disable=invalid-name
    """Get scheduler configs matching an event provided on stdin"""
    opt_args = Command.opt_args + [
        Args.indent,
        {
            'name': '--channel',
            'help': "Name of the pub/sub channel, or 'node' by default",
        },
    ]

    def __call__(self, configs, args):
        rconfigs = configs['runtimes']
        runtimes = dict(kernelci.runtime.get_all_runtimes(rconfigs, args))
        sched = kernelci.scheduler.Scheduler(configs, runtimes)
        event = json.loads(sys.stdin.read())
        channel = args.channel or 'node'
        for job, runtime, platform in sched.get_schedule(event, channel):
            print(f"{job.name:32} {runtime.config.name:32} {platform.name}")
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("config", globals(), args)
