# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI pipeline job configuration"""

from kernelci.config.base import YAMLConfigObject


class Job(YAMLConfigObject):
    """Pipeline job definition"""

    yaml_tag = '!Job'

    # pylint: disable=too-many-arguments
    def __init__(self, name, template, image=None,
                 run_on=None, params=None):
        self._name = name
        self._template = template
        self._image = image
        self._run_on = run_on or []
        self._params = params or {}

    @property
    def name(self):
        """Job name"""
        return self._name

    @property
    def template(self):
        """Template file name"""
        return self._template

    @property
    def image(self):
        """Runtime environment image name"""
        return self._image

    @property
    def run_on(self):
        """Criteria for the job to be run"""
        return list(dict(crit) for crit in self._run_on)

    @property
    def params(self):
        """Arbitrary parameters passed to the template"""
        return dict(self._params)

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'template', 'image', 'run_on', 'params'})
        return attrs


def from_yaml(data, _):
    """Create the pipeline job definitions using data loaded from YAML"""
    jobs = {
        name: Job.load_from_yaml(config, name=name)
        for name, config in data.get('jobs', {}).items()
    }

    return {
        'jobs': jobs,
    }
