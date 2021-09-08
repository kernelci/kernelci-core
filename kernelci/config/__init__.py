# Copyright (C) 2021 Collabora Limited
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

import glob
import os
import yaml

import kernelci.config
import kernelci.config.build
import kernelci.config.data
import kernelci.config.lab
import kernelci.config.rootfs
import kernelci.config.test
import kernelci.config.firmware


def load_yaml(config_path):
    """Load the YAML configuration

    Load all the YAML files found in the configuration directory into a single
    dictionary and return it.  Entries that have a same name in multiple files
    will be merged together under the same top-level dictionary key.

    *config_path* is the path to the YAML config directory, or alternative a
                  single YAML file
    """
    if config_path.endswith('.yaml'):
        yaml_files = [config_path]
    else:
        yaml_files = glob.glob(os.path.join(config_path, "*.yaml"))
    config = dict()
    for yaml_path in yaml_files:
        with open(yaml_path) as yaml_file:
            data = yaml.safe_load(yaml_file)
            for k, v in data.items():
                config_value = config.setdefault(k, v.__class__())
                if hasattr(config_value, 'update'):
                    config_value.update(v)
                elif hasattr(config_value, 'extend'):
                    config_value.extend(v)
                else:
                    config[k] = v
    return config


def from_data(data):
    """Create configuration objects from the YAML data

    Create a top-level dictionary with all the configuration objects using the
    provided data dictionary loaded from YAML and return it.

    *data* is the configuration dictionary loaded from YAML
    """
    config = dict()
    config.update(kernelci.config.build.from_yaml(data))
    config.update(kernelci.config.data.from_yaml(data))
    config.update(kernelci.config.lab.from_yaml(data))
    config.update(kernelci.config.rootfs.from_yaml(data))
    config.update(kernelci.config.test.from_yaml(data))
    config.update(kernelci.config.firmware.from_yaml(data))
    return config


def load(config_path):
    """Load the configuration from YAML files

    Load all the YAML files found in the configuration directory then create
    a dictionary containing the configuration objects and return it.

    *config_path* is the path to the YAML config directory
    """
    data = load_yaml(config_path)
    return from_data(data)
