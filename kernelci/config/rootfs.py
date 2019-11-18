# Copyright (C) 2019 Collabora Limited
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

from kernelci.config import YAMLObject


class RootFS(YAMLObject):
    def __init__(self, name, rootfs_type):
        self._name = name
        self._rootfs_type = rootfs_type

    @classmethod
    def from_yaml(cls, rootfs, kw):
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def rootfs_type(self):
        return self._rootfs_type


class RootFS_Debos(RootFS):
    def __init__(self, *args, **kwargs):
        super(RootFS_Debos, self).__init__(*args, **kwargs)

    @classmethod
    def from_yaml(cls, name, kw):
        return cls(**kw)


class RootFSFactory(YAMLObject):
    _rootfs_types = {
        'debos': RootFS_Debos
    }

    @classmethod
    def from_yaml(cls, name, rootfs):
        rootfs_type = rootfs.get('rootfs_type')
        kw = {
            'name': name,
            'rootfs_type': rootfs_type,
        }
        rootfs_cls = cls._rootfs_types[rootfs_type] if rootfs_type else RootFS
        return rootfs_cls.from_yaml(rootfs, kw)


def from_yaml(yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    rootfs_configs = {
        name: RootFSFactory.from_yaml(name, rootfs)
        for name, rootfs in data['rootfs_configs'].iteritems()
    }

    config_data = {
        'rootfs_configs': rootfs_configs,
    }

    return config_data
