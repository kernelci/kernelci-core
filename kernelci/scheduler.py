# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI Pipeline scheduler logic"""

import random

import kernelci.runtime


class Scheduler:
    """Core logic for implementing a pipeline scheduler

    Using the YAML configuration and an optional list of runtimes to narrow
    down the scope, this class can be used to determine which jobs to run in
    which runtimes and on which platforms based on an event received from the
    API via the Pub/Sub interface.
    """

    def __init__(self, configs, runtimes_list=None):
        self._scheduler = configs['scheduler']
        self._jobs = configs['jobs']
        self._runtimes_by_name = {
            config_name: kernelci.runtime.get_runtime(config)
            for config_name, config in configs['runtimes'].items()
            if not runtimes_list or config_name in runtimes_list
        }
        self._runtimes_by_type = {}
        for _, runtime in self._runtimes_by_name.items():
            runtime_type = self._runtimes_by_type.setdefault(
                runtime.config.lab_type, []
            )
            runtime_type.append(runtime)
        self._platforms = configs['device_types']

    def get_jobs(self, event, channel='node'):
        """Get the job configs matching a given event"""
        for _, job in self._jobs.items():
            for run_on in job.run_on:
                run_on_channel = run_on.get('channel')
                if run_on_channel == channel:
                    run_on = run_on.copy()
                    run_on.pop('channel')
                    if run_on.items() <= event.items():
                        yield job

    def get_configs(self, event, channel='node'):
        """Get the scheduler configs to run jobs matching a given event"""
        for job in self.get_jobs(event, channel):
            for entry in self._scheduler:
                if entry.job == job.name:
                    yield entry

    def get_schedule(self, event, channel='node'):
        """Get the (job, runtime, platform) configs for each job to run"""
        for config in self.get_configs(event, channel):
            runtime_name = config.runtime.get('name')
            runtime_type = config.runtime.get('type')
            if runtime_name:
                runtime = self._runtimes_by_name.get(runtime_name)
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
