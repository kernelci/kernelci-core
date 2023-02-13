# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI Runtime environment configuration"""

from kernelci.config.base import FilterFactory, _YAMLObject


class Runtime(_YAMLObject):
    """Runtime environment configuration"""

    def __init__(self, name, lab_type, filters=None):
        """A runtime environment configuration object

        *name* is the name used to refer to the lab in meta-data.
        *lab_type* is the name of the type of lab, essentially indicating the
                   type of software used by the lab.
        *filters* is a list of Filter objects associated with this lab.
        """
        self._name = name
        self._lab_type = lab_type
        self._filters = filters or []

    @property
    def name(self):
        """Configuration name"""
        return self._name

    @property
    def lab_type(self):
        """Runtime environment name"""
        return self._lab_type

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'lab_type'})
        return attrs

    def match(self, data):
        """Match configuration filters with provided input data"""
        return all(f.match(**data) for f in self._filters)


class RuntimeLAVA(Runtime):
    """Configuration for LAVA runtime environments"""

    PRIORITIES = {
        'low': 0,
        'medium': 50,
        'high': 100,
    }

    # This should be solved by dropping the "priority" attribute
    # pylint: disable=too-many-arguments
    def __init__(self, url, priority=None, priority_min=None,
                 priority_max=None, queue_timeout=None, **kwargs):
        super().__init__(**kwargs)

        def _set_priority_value(value, default):
            return max(min(value, 100), 0) if value is not None else default

        self._url = url
        self._priority = self.PRIORITIES.get(priority, priority)
        self._priority_min = _set_priority_value(priority_min, self._priority)
        self._priority_max = _set_priority_value(priority_max, self._priority)
        self._queue_timeout = queue_timeout

    @property
    def url(self):
        """URL of the LAVA API"""
        return self._url

    @property
    def priority(self):
        """Job priority for the lab"""
        return self._priority

    @property
    def priority_min(self):
        """Minimum job priority for the lab"""
        return self._priority_min

    @property
    def priority_max(self):
        """Maximum job priority for the lab"""
        return self._priority_max

    @property
    def queue_timeout(self):
        """Queue timeout duration for the lab

        The units are passed as a dictionary e.g. days and hours attributes
        with respective values.
        """
        return self._queue_timeout

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({
            'priority',
            'priority_min',
            'priority_max',
            'queue_timeout',
            'url',
        })
        return attrs


class RuntimeKubernetes(Runtime):
    """Configuration for Kubernetes runtime environments"""

    def __init__(self, context=None, **kwargs):
        super().__init__(**kwargs)
        self._context = context

    @property
    def context(self):
        """Name of the Kubernetes context to use e.g. with kubectl"""
        return self._context

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'context'})
        return attrs


class RuntimeFactory:  # pylint: disable=too-few-public-methods
    """Factory to create lab objects from YAML data."""

    _lab_types = {
        'kubernetes': RuntimeKubernetes,
        'lava.lava_xmlrpc': RuntimeLAVA,
        'lava.lava_rest': RuntimeLAVA,
        'shell': Runtime,
    }

    @classmethod
    def from_yaml(cls, name, config, default_filters):
        """Load the configuration from YAML data"""
        lab_type = config.get('lab_type')
        kwargs = {
            'name': name,
            'lab_type': lab_type,
            'filters': FilterFactory.from_data(config, default_filters),
        }
        lab_cls = cls._lab_types[lab_type] if lab_type else Runtime
        return lab_cls.from_yaml(config, **kwargs)


def from_yaml(data, filters):
    """Load the runtime environment from YAML based on its type"""
    runtimes_filters = filters.get('runtimes')
    runtimes = {
        name: RuntimeFactory.from_yaml(name, runtime, runtimes_filters)
        for name, runtime in data.get('runtimes', {}).items()
    }

    return {
        'runtimes': runtimes,
    }
