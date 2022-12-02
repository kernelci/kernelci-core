# Copyright (C) 2022 Collabora Limited
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

from kernelci.config.base import YAMLObject


class Storage(YAMLObject):
    """Base configuration class for Storage implementations"""

    def __init__(self, name, storage_type, base_url):
        """Storage configuration class

        *name* is the name of the storage configuration
        *storage_type* is the type of storage implementation
        *base_url* is the public base URL for retrieving artifacts
        """
        self._name = name
        self._storage_type = storage_type
        self._base_url = base_url

    @classmethod
    def get_kwargs(cls, config):
        return {}

    @property
    def name(self):
        return self._name

    @property
    def storage_type(self):
        return self._storage_type

    @property
    def base_url(self):
        return self._base_url


class Storage_backend(Storage):

    def __init__(self, api_url, *args, **kwargs):
        """Configuration for kernelci_backend storage

        *api_url* is the URL to access the kernelci-backend API
        """
        super().__init__(*args, **kwargs)
        self._api_url = api_url

    @classmethod
    def get_kwargs(cls, config):
        return cls._kw_from_yaml(config, ['api_url'])

    @property
    def api_url(self):
        return self._api_url


class Storage_ssh(Storage):

    def __init__(self, host, port=22, user='kernelci', path='~/data',
                 *args, **kwargs):
        """Configuration for SSH storage

        *host* is the hostname of the SSH server
        *port* is the port number of the SSH server
        *user* is the user name to connect to the SSH server
        *path* is the base destination path on the SSH server
        """
        super().__init__(*args, **kwargs)
        self._host = host
        self._port = port
        self._user = user
        self._path = path

    @classmethod
    def get_kwargs(cls, config):
        return cls._kw_from_yaml(config, ['host', 'port', 'user', 'path'])

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def user(self):
        return self._user

    @property
    def path(self):
        return self._path


class StorageFactory(YAMLObject):
    """Factory to create storage objects from YAML data."""

    _storage_types = {
        'backend': Storage_backend,
        'ssh': Storage_ssh,
    }

    @classmethod
    def from_yaml(cls, name, config):
        storage_type = config.get('storage_type')
        storage_cls = cls._storage_types[storage_type]
        kw = {
            'name': name,
            'storage_type': storage_type,
        }
        kw.update(cls._kw_from_yaml(config, ['base_url']))
        kw.update(storage_cls.get_kwargs(config))
        return storage_cls(**kw)


def from_yaml(data, filters):
    storage_configs = {
        name: StorageFactory.from_yaml(name, storage)
        for name, storage in data.get('storage_configs', {}).items()
    }

    return {
        'storage_configs': storage_configs,
    }
