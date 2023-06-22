# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI Pipeline scheduler logic"""

import random


class Scheduler:
    """Core logic for implementing a pipeline scheduler

    Using the YAML configuration and an optional list of runtimes to narrow
    down the scope, this class can be used to determine which jobs to run in
    which runtimes and on which platforms based on an event received from the
    API via the Pub/Sub interface.
    """

    def __init__(self, configs, runtimes):
        self._scheduler = configs['scheduler']
        self._jobs = configs['jobs']
        self._runtimes = runtimes
        self._runtimes_by_type = {}
        for _, runtime in self._runtimes.items():
            runtime_type = self._runtimes_by_type.setdefault(
                runtime.config.lab_type, []
            )
            runtime_type.append(runtime)
        self._platforms = configs['device_types']

    def get_configs(self, event, channel='node'):
        """Get the scheduler configs matching a given event"""
        for entry in self._scheduler:
            sched_event_channel = entry.event.get('channel')
            if sched_event_channel == channel:
                sched_event = entry.event.copy()
                sched_event.pop('channel')
                if sched_event.items() <= event.items():
                    yield entry

    def get_schedule(self, event, channel='node'):
        """Get the (job, runtime, platform) configs for each job to run"""
        for config in self.get_configs(event, channel):
            runtime_name = config.runtime.get('name')
            runtime_type = config.runtime.get('type')
            if runtime_name:
                runtime = self._runtimes.get(runtime_name)
            elif runtime_type:
                # Pick one at random until there's more criteria
                runtimes = self._runtimes_by_type.get(runtime_type)
                runtime = random.sample(runtimes, 1)[0] if runtimes else None
            job = self._jobs.get(config.job)
            if not all((job, runtime)):
                continue
            platforms = config.platforms or [runtime.config.lab_type]
            for platform_name in platforms:
                platform = self._platforms.get(platform_name)
                if platform:
                    yield job, runtime, platform
