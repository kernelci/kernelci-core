# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API object configuration"""

from kernelci.config.base import YAMLConfigObject


class API(YAMLConfigObject):
    """Base KernelCI API configuration object"""

    yaml_tag = '!API'

    def __init__(self, name, url, version='latest'):
        self._name = name
        self._url = url
        self._version = version

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

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'url', 'version'})
        return attrs

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                'url': data.url,
                'version': data.version,
            }
        )


def from_yaml(data, _):
    """Create the API configs using data loaded from YAML"""
    api_configs = {
        name: API.load_from_yaml(config, name=name)
        for name, config in data.get('api_configs', {}).items()
    }

    return {
        'api_configs': api_configs,
    }
