# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI pipeline job configuration"""

from .base import YAMLConfigObject


class Job(YAMLConfigObject):
    """Pipeline job definition"""

    yaml_tag = '!Job'

    # pylint: disable=too-many-arguments
    def __init__(self, name, template, kind="node", image=None, params=None, rules=None,
                 kcidb_test_suite=None):
        self._name = name
        self._template = template
        self._kind = kind
        self._image = image
        self._kcidb_test_suite = kcidb_test_suite
        self._params = self.format_params(params.copy(), params) if params else {}
        self._rules = rules

    @property
    def name(self):
        """Job name"""
        return self._name

    @property
    def template(self):
        """Template file name"""
        return self._template

    @property
    def kind(self):
        """Job node kind"""
        return self._kind

    @property
    def image(self):
        """Runtime environment image name"""
        return self._image

    @property
    def params(self):
        """Arbitrary parameters passed to the template"""
        return dict(self._params)

    @property
    def rules(self):
        """Kernel requirements (tree, branch, version...)"""
        return self._rules

    @property
    def kcidb_test_suite(self):
        """Mapping of KernelCI test to KCIDB test suite"""
        return self._kcidb_test_suite

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'template', 'kind', 'image', 'params', 'rules', 'kcidb_test_suite'})
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
