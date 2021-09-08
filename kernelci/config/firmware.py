# Copyright (C) 2020 Collabora Limited
# Author: Adrian Ratiu <adrian.ratiu@collabora.com>
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


class DeviceFirmware(YAMLObject):

    def __init__(self, name, files=None):
        self._name = name
        self._files = files or list()

    @property
    def name(self):
        return self._name

    @property
    def files(self):
        return self._files


def from_yaml(data):
    fw_archives = {
        name: DeviceFirmware(name, config)
        for name, config in data['firmware_archives'].items()
    }

    config_data = {
        'firmware_configs': fw_archives
    }

    return config_data
