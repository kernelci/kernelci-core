# Copyright (C) 2019 Collabora Limited
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

from kernelci.config.base import FilterFactory, YAMLObject


class Lab(YAMLObject):
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

    @classmethod
    def from_yaml(cls, lab, kw):
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def lab_type(self):
        return self._lab_type

    def match(self, data):
        return all(f.match(**data) for f in self._filters)


class LabAPI(Lab):

    def __init__(self, url, *args, **kwargs):
        """
        *url* is the URL to reach the lab API.
        """
        super().__init__(*args, **kwargs)
        self._url = url

    @property
    def url(self):
        return self._url


class Lab_LAVA(LabAPI):

    def __init__(self, priority='medium', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._priority = priority

    @property
    def priority(self):
        return self._priority

    @classmethod
    def from_yaml(cls, lab, kw):
        priority = lab.get('priority')
        if priority:
            kw['priority'] = priority
        return cls(**kw)


class LabFactory(YAMLObject):
    """Factory to create lab objects from YAML data."""

    _lab_types = {
        'lava.lava_xmlrpc': Lab_LAVA,
        'lava.lava_rest': Lab_LAVA,
        'shell': Lab,
    }

    @classmethod
    def from_yaml(cls, name, lab):
        lab_type = lab.get('lab_type')
        kw = {
            'name': name,
            'lab_type': lab_type,
            'filters': FilterFactory.from_data(lab),
        }
        kw.update(cls._kw_from_yaml(lab, [
            'url',
        ]))
        lab_cls = cls._lab_types[lab_type] if lab_type else Lab
        return lab_cls.from_yaml(lab, kw)


def from_yaml(data, filters):
    labs = {
        name: LabFactory.from_yaml(name, lab)
        for name, lab in data.get('labs', {}).items()
    }

    return {
        'labs': labs,
    }
