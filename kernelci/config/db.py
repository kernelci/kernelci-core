# Copyright (C) 2020-2023 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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

from kernelci.config.base import _YAMLObject


class Database(_YAMLObject):

    def __init__(self, name, db_type):
        self._name = name
        self._db_type = db_type

    @property
    def name(self):
        return self._name

    @property
    def db_type(self):
        return self._db_type

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'db_type'})
        return attrs


class DatabaseAPI(Database):

    def __init__(self, name, db_type, url):
        super().__init__(name, db_type)
        self._url = url

    @property
    def url(self):
        return self._url

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'url'})
        return attrs


class DatabaseFactory(_YAMLObject):
    _db_types = {
        "kernelci_backend": DatabaseAPI,
        "kernelci_api": DatabaseAPI,
    }

    @classmethod
    def from_yaml(cls, config, name):
        db_type = config.get('db_type')
        if db_type is None:
            raise TypeError("db_type cannot be Empty")

        db_cls = cls._db_types.get(db_type)
        if db_cls is None:
            raise ValueError("Unsupported database type: {}".format(db_type))

        return db_cls.from_yaml(config, name=name)


def from_yaml(data, filters):
    db_configs = {
        name: DatabaseFactory.from_yaml(db, name)
        for name, db in data.get('db_configs', {}).items()
    }

    return {
        'db_configs': db_configs,
    }
