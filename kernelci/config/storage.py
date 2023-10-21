# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API object configuration"""

from .base import YAMLConfigObject


class Storage(YAMLConfigObject):
    """Base configuration class for Storage implementations"""

    yaml_tag = '!Storage'

    def __init__(self, name, storage_type, base_url):
        """Storage configuration class

        *name* is the name of the storage configuration
        *storage_type* is the type of storage implementation
        *base_url* is the public base URL for retrieving artifacts
        """
        self._name = name
        self._storage_type = storage_type
        self._base_url = base_url

    @property
    def name(self):
        """Storage config name"""
        return self._name

    @property
    def storage_type(self):
        """Storage config type name"""
        return self._storage_type

    @property
    def base_url(self):
        """Base URL for HTTP(s) downloads"""
        return self._base_url

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'storage_type', 'base_url'})
        return attrs


class AzureFilesStorage(Storage):
    """Azure Files storage configuration

    *share* is the name of the Azure Files share
    *sas_public_token* is the read-only SAS token used in public URLs for
    downloads
    """

    yaml_tag = '!AzureFilesStorage'

    def __init__(self, share, sas_public_token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._share = share
        self._sas_public_token = sas_public_token

    @property
    def share(self):
        """Name of the Azure Files share to use"""
        return self._share

    @property
    def sas_public_token(self):
        """Public SAS token used in download URLs"""
        return self._sas_public_token

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'share', 'sas_public_token'})
        return attrs


class BackendStorage(Storage):
    """Storage configuration for the legacy kernelci-backend

    *api_url* is the URL to access the kernelci-backend API
    """

    yaml_tag = '!BackendStorage'

    def __init__(self, api_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_url = api_url

    @property
    def api_url(self):
        """Backend API URL used for uploads"""
        return self._api_url

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'api_url'})
        return attrs


class SSHStorage(Storage):
    """SSH storage configuration

    *host* is the hostname of the SSH server
    *port* is the port number of the SSH server
    *user* is the user name to connect to the SSH server
    *path* is the base destination path on the SSH server
    """

    yaml_tag = '!SSHStorage'

    def __init__(self, host, *args, port=22, user='kernelci', path='~/data',
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._host = host
        self._port = port
        self._user = user
        self._path = path

    @property
    def host(self):
        """SSH host name"""
        return self._host

    @property
    def port(self):
        """SSH port number"""
        return self._port

    @property
    def user(self):
        """SSH user name"""
        return self._user

    @property
    def path(self):
        """SSH upload path on the destination host"""
        return self._path

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'host', 'port', 'user', 'path'})
        return attrs


class StorageFactory:  # pylint: disable=too-few-public-methods
    """Factory to create storage objects from YAML data."""

    _storage_types = {
        'azure': AzureFilesStorage,
        'backend': BackendStorage,
        'ssh': SSHStorage,
    }

    @classmethod
    def from_yaml(cls, name, config):
        """Load configuration for matching storage type from YAML data"""
        storage_type = config.get('storage_type')
        storage_cls = cls._storage_types[storage_type]
        kwargs = {
            'name': name,
            'storage_type': storage_type,
        }
        return storage_cls.load_from_yaml(config, **kwargs)


def from_yaml(data, _):
    """Load storage configuration from YAML data"""
    storage_configs = {
        name: StorageFactory.from_yaml(name, storage)
        for name, storage in data.get('storage', {}).items()
    }
    legacy_storage_configs = {
        name: StorageFactory.from_yaml(name, storage)
        for name, storage in data.get('storage_configs', {}).items()
    }
    storage_configs.update(legacy_storage_configs)

    return {
        'storage_configs': storage_configs,  # deprecated
        'storage': storage_configs,
    }
