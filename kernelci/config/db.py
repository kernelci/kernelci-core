# Copyright (C) 2020 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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

from kernelci.config.base import YAMLObject


class Database(YAMLObject):
    def __init__(self, name, db_type):
        self._name = name
        self._db_type = db_type

    @classmethod
    def from_yaml(cls, db, kw):
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def db_type(self):
        return self._db_type

    def _get_attrs(self):
        attrs = super()._get_attrs()
        attrs.update({'name', 'db_type'})
        return attrs


class DatabaseAPI(Database):
    def __init__(self, name, db_type, url):
        super().__init__(name, db_type)
        self._url = url

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(config, [
            'db_type', 'url',
        ]))
        return cls(**kw)

    @property
    def url(self):
        return self._url

    def _get_attrs(self):
        attrs = super()._get_attrs()
        attrs.update({'url'})
        return attrs


class DatabaseFactory(YAMLObject):
    _db_types = {
        "kernelci_backend": DatabaseAPI,
        "kernelci_api": DatabaseAPI,
    }

    @classmethod
    def from_yaml(cls, name, db):
        db_type = db.get('db_type')
        if db_type is None:
            raise TypeError("db_type cannot be Empty")

        db_cls = cls._db_types.get(db_type)
        if db_cls is None:
            raise ValueError("Unsupported database type: {}".format(db_type))

        return db_cls.from_yaml(db, name)


def from_yaml(data, filters):
    db_configs = {
        name: DatabaseFactory.from_yaml(name, db)
        for name, db in data.get('db_configs', {}).items()
    }

    return {
        'db_configs': db_configs,
    }
