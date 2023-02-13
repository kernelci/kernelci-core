# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import yaml

from kernelci.config.base import FilterFactory, _YAMLObject


class Runtime(_YAMLObject):
    """Test lab model."""

    def __init__(self, name, lab_type, filters=None):
        """A lab object contains all the information relative to a test lab.

        *name* is the name used to refer to the lab in meta-data.
        *lab_type* is the name of the type of lab, essentially indicating the
                   type of software used by the lab.
        *filters* is a list of Filter objects associated with this lab.
        """
        self._name = name
        self._lab_type = lab_type
        self._filters = filters or list()

    @property
    def name(self):
        return self._name

    @property
    def lab_type(self):
        return self._lab_type

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'lab_type'})
        return attrs

    def match(self, data):
        return all(f.match(**data) for f in self._filters)


class Runtime_LAVA(Runtime):

    PRIORITIES = {
        'low': 0,
        'medium': 50,
        'high': 100,
    }

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
        return self._url

    @property
    def priority(self):
        return self._priority

    @property
    def priority_min(self):
        return self._priority_min

    @property
    def priority_max(self):
        return self._priority_max

    @property
    def queue_timeout(self):
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


class Runtime_Kubernetes(Runtime):

    def __init__(self, context=None, **kwargs):
        super().__init__(**kwargs)
        self._context = context

    @property
    def context(self):
        return self._context

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'context'})
        return attrs


class RuntimeFactory(_YAMLObject):
    """Factory to create lab objects from YAML data."""

    _lab_types = {
        'kubernetes': Runtime_Kubernetes,
        'lava.lava_xmlrpc': Runtime_LAVA,
        'lava.lava_rest': Runtime_LAVA,
        'shell': Runtime,
    }

    @classmethod
    def from_yaml(cls, name, config):
        lab_type = config.get('lab_type')
        kw = {
            'name': name,
            'lab_type': lab_type,
            'filters': FilterFactory.from_data(config),
        }
        lab_cls = cls._lab_types[lab_type] if lab_type else Runtime
        return lab_cls.from_yaml(config, **kw)


def from_yaml(data, filters):
    labs = {
        name: RuntimeFactory.from_yaml(name, lab)
        for name, lab in data.get('labs', {}).items()
    }

    return {
        'labs': labs,
    }
