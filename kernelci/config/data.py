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


class Backend(Database):
    def __init__(self, name, db_type, url):
        super().__init__(name, db_type)
        self._url = url

    @classmethod
    def from_yaml(cls, config, name):
        kw = name
        kw.update(cls._kw_from_yaml(
            config, ['name', 'url']))
        return cls(**kw)

    @property
    def url(self):
        return self._url


class DatabaseFactory(YAMLObject):
    _db_types = {
        "kernelci_backend": Backend
    }

    @classmethod
    def from_yaml(cls, name, db):
        db_type = db.get('db_type')
        if db_type is None:
            raise TypeError("db_type cannot be Empty")
        elif db_type not in cls._db_types:
            raise ValueError("Unsupported database type: {}".format(db_type))
        else:
            kw = {
                'name': name,
                'db_type': db_type,
                }
        db_cls = cls._db_types[db_type] if db_type else Database
        return db_cls.from_yaml(db, kw)


def from_yaml(data):
    db_configs = {
        name: DatabaseFactory.from_yaml(name, db)
        for name, db in data['db_configs'].items()
    }

    config_data = {
        'db_configs': db_configs,
    }
    return config_data
