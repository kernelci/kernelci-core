# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API object configuration"""

from .base import YAMLConfigObject


class API(YAMLConfigObject):
    """Base KernelCI API configuration object"""

    yaml_tag = '!API'

    def __init__(self, name, url, version='latest', timeout=60):
        self._name = name
        self._url = url
        self._version = version
        self._timeout = timeout

    @property
    def name(self):
        """Name of the API configuration or instance"""
        return self._name

    @property
    def url(self):
        """Full URL to use the API"""
        return self._url

    @property
    def version(self):
        """API version"""
        return self._version

    @property
    def timeout(self):
        """HTTP request timeout in seconds"""
        return self._timeout

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'url', 'version', 'timeout'})
        return attrs


def from_yaml(data, _):
    """Create the API configs using data loaded from YAML"""
    api_configs = {
        name: API.load_from_yaml(config, name=name)
        for name, config in data.get('api', {}).items()
    }

    return {
        'api': api_configs,
    }
