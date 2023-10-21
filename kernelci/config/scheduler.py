# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI scheduler configuration"""

from .base import YAMLConfigObject


class SchedulerEntry(YAMLConfigObject):
    """Scheduler entry definition"""

    yaml_tag = '!SchedulerEntry'

    def __init__(self, job, runtime, event, platforms=None):
        self._job = job
        self._runtime = runtime
        self._event = event
        self._platforms = platforms or []

    @property
    def job(self):
        """Name of the job"""
        return self._job

    @property
    def runtime(self):
        """Runtime parameters (name or type)"""
        return dict(self._runtime)

    @property
    def event(self):
        """Criteria for an event to cause the job to be run"""
        return dict(self._event)

    @property
    def platforms(self):
        """List of platform names"""
        return list(self._platforms)

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'job', 'runtime', 'event', 'platforms'})
        return attrs


def from_yaml(data, _):
    """Create the pipeline scheduler definitions using data loaded from YAML"""
    scheduler = [
        SchedulerEntry.load_from_yaml(config)
        for config in data.get('scheduler', {})
    ]

    return {
        'scheduler': scheduler,
    }
