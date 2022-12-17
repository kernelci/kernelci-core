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

import kernelci
import kernelci.config
import kernelci.config.build
import kernelci.config.db
import kernelci.config.lab
import kernelci.config.rootfs
import kernelci.config.storage
import kernelci.config.test


def _iterate_yaml_files(config_path):
    if config_path.endswith('.yaml'):
        yaml_files = [config_path]
    else:
        yaml_files = glob.glob(os.path.join(config_path, "*.yaml"))
    for yaml_path in yaml_files:
        with open(yaml_path) as yaml_file:
            data = yaml.safe_load(yaml_file)
            yield yaml_path, data


def validate_yaml(config_path, entries):
    for yaml_path, data in _iterate_yaml_files(config_path):
        for name, value in ((k, v) for k, v in data.items() if k in entries):
            if isinstance(value, dict):
                keys = value.keys()
            elif isinstance(value, list):
                keys = value
            else:
                keys = []
            err = kernelci.sort_check(keys)
            if err:
                return "Broken order in {} {}: '{}' is before '{}'".format(
                    yaml_path, name, err[0], err[1])
    return None


def load_yaml(config_path, validate_entries=None):
    """Load the YAML configuration

    Load all the YAML files found in the configuration directory into a single
    dictionary and return it.  Entries that have a same name in multiple files
    will be merged together under the same top-level dictionary key.

    *config_path* is the path to the YAML config directory, or alternative a
                  single YAML file.

    *validate_entries* is currently unused.
    """
    config = dict()
    for yaml_path, data in _iterate_yaml_files(config_path):
        for name, value in data.items():
            config_value = config.setdefault(name, value.__class__())
            if hasattr(config_value, 'update'):
                config_value.update(value)
            elif hasattr(config_value, 'extend'):
                config_value.extend(value)
            else:
                config[name] = value
    return config


def _merge_trees(old, update):
    """Merge two values loaded from YAML

    This combines two values recursively that have been loaded from
    YAML.  The data from *update* will be overlaid onto *old*
    according to the rules:

    - If *old* and *update* are dictionaries, their keys will be
      unified, with the values for any keys present in both
      dictionaries being merged recursively.

    - If *old* and *update* are lists, the result is the concatenation
      of the two lists.

    - Otherwise, *update* replaces *old*.

    Neither *old* nor *update* is modified; any modifications required
    lead to a new value being returned.

    """
    if isinstance(old, dict) and isinstance(update, dict):
        res = dict()
        for k in (set(old) | set(update)):
            if (k in old) and (k in update):
                res[k] = _merge_trees(old[k], update[k])
            elif k in old:
                res[k] = old[k]
            else:
                res[k] = update[k]
        return res
    elif isinstance(old, list) and isinstance(update, list):
        return old + update
    else:
        return update


def load_all_yaml(config_paths, validate_entries=None):
    """Load the YAML configuration

    Load all the YAML files in all the specific configuration
    directories and aggregate them together. Later directories take
    precedence over earlier ones. This enables combining sources of
    configuration data from multiple places.

    *config_paths* is an ordered list of YAML configuration
                   directories or YAML files, with later entries
                   having higher priority.

    *validate_entries* is passed to `load_yaml()`

    """
    config = dict()
    for path in config_paths:
        data = load_yaml(path, validate_entries)
        config = _merge_trees(config, data)
    return config


def from_data(data):
    """Create configuration objects from the YAML data

    Create a top-level dictionary with all the configuration objects using the
    provided data dictionary loaded from YAML and return it.

    *data* is the configuration dictionary loaded from YAML
    """
    config = dict()
    filters = kernelci.config.base.default_filters_from_yaml(data)
    config.update(kernelci.config.build.from_yaml(data, filters))
    config.update(kernelci.config.db.from_yaml(data, filters))
    config.update(kernelci.config.lab.from_yaml(data, filters))
    config.update(kernelci.config.rootfs.from_yaml(data, filters))
    config.update(kernelci.config.storage.from_yaml(data, filters))
    config.update(kernelci.config.test.from_yaml(data, filters))
    return config


def load(config_path):
    """Load the configuration from YAML files

    Load all the YAML files found in the configuration directory then create
    a dictionary containing the configuration objects and return it.

    *config_path* is the path to the YAML config directory or a
    unified file

    """
    if not config_path:
        return {}
    data = load_yaml(config_path)
    return from_data(data)


def load_all(config_paths):
    """Load the configuration from YAML files

    Load all the YAML files found in all the configuration
    directories, then create a dictionary containing the configuration
    objects and return it. Note that the config paths are in priority
    order, with later entries overriding earlier ones.

    *config_paths* is a list of YAML config directories (or unified
     files)

    """
    data = load_all_yaml(config_paths)
    return from_data(data)
