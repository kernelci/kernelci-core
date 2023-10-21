# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI YAML pipeline configuration"""

import glob
import importlib
import os
import yaml

import kernelci
from .base import default_filters_from_yaml


def iterate_yaml_files(config_path: str):
    """Load all the YAML files found in config_path

    The `config_path` can be either a single file if it ends with .yaml or a
    directory path where to find multiple YAML files recursively.  Then iterate
    over the file(s) as (path, data) 2-tuples.
    """
    if config_path.endswith('.yaml'):
        yaml_files = [config_path]
    else:
        yaml_files = glob.glob(os.path.join(config_path, "*.yaml"))
    for yaml_path in yaml_files:
        with open(yaml_path, encoding='utf8') as yaml_file:
            data = yaml.safe_load(yaml_file)
            yield yaml_path, data


def get_config_paths(config_paths):
    """Get the list of all YAML files to be loaded"""
    if not config_paths:
        config_paths = []
        for config_path in ['config/core', '/etc/kernelci/core']:
            if os.path.isdir(config_path):
                config_paths.append(config_path)
                break
    elif isinstance(config_paths, str):
        config_paths = [config_paths]
    return config_paths


def validate_yaml(config_paths, entries):
    """Load all the YAML config and validate the data integrity"""
    error = None
    try:
        for path in get_config_paths(config_paths):
            for yaml_path, data in iterate_yaml_files(path):
                for name, value in (
                        (k, v) for k, v in data.items() if k in entries):
                    if isinstance(value, dict):
                        keys = value.keys()
                    elif isinstance(value, list):
                        keys = (
                            [] if len(value) and isinstance(value[0], dict)
                            else value
                        )
                    else:
                        keys = []
                    err = kernelci.sort_check(keys)
                    if err:
                        error = \
                            f"Broken order in {yaml_path} {name}: "\
                            f"'{err[0]}' is before '{err[1]}'"
                        break
    except yaml.scanner.ScannerError as exc:
        error = str(exc)
    return error


def load_single_yaml(config_path):
    """Load the YAML configuration from a single directory or file

    Load all the YAML files found in a configuration directory or single file
    into a dictionary and return it.  Entries that have a same name in multiple
    files will be merged together under the same top-level dictionary key.

    *config_path* is the path to the YAML config directory, or alternative a
                  single YAML file.
    """
    config = {}
    for _, data in iterate_yaml_files(config_path):
        for name, value in data.items():
            config_value = config.setdefault(name, value.__class__())
            if hasattr(config_value, 'update'):
                config_value.update(value)
            elif hasattr(config_value, 'extend'):
                config_value.extend(value)
            else:
                config[name] = value
    return config


def merge_trees(old, update):
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
        merged = {}
        for k in (set(old) | set(update)):
            if (k in old) and (k in update):
                merged[k] = merge_trees(old[k], update[k])
            elif k in old:
                merged[k] = old[k]
            else:
                merged[k] = update[k]
    elif isinstance(old, list) and isinstance(update, list):
        merged = old + update
    else:
        merged = update
    return merged


def load_yaml(config_paths):
    """Load the YAML configuration

    Load all the YAML files in all the specific configuration directories or
    files and aggregate them together.  Later paths take precedence over
    earlier ones.  This enables combining sources of configuration data from
    multiple places.

    *config_paths* is a single string or an ordered list of YAML configuration
                   directories or YAML files, with later entries having higher
                   priority.
    """
    if not isinstance(config_paths, list):
        config_paths = [config_paths]
    config = {}
    for path in config_paths:
        data = load_single_yaml(path)
        config = merge_trees(config, data)
    return config


def load_data(data):
    """Create configuration objects from the YAML data

    Create a top-level dictionary with all the configuration objects using the
    provided data dictionary loaded from YAML and return it.

    *data* is the configuration dictionary loaded from YAML
    """
    config = {}
    filters = default_filters_from_yaml(data)
    for module in [
        'kernelci.config.api',
        'kernelci.config.job',
        'kernelci.config.runtime',
        'kernelci.config.scheduler',
        'kernelci.config.storage',
        'kernelci.legacy.config',
    ]:
        mod = importlib.import_module(module)
        config.update(mod.from_yaml(data, filters))
    return config


def load(config_paths):
    """Load the configuration from YAML files

    Load all the YAML files found in the configuration directories then create
    a dictionary containing the configuration objects and return it.  Note that
    the config paths are in priority order, with later entries overriding
    earlier ones.

    *config_paths* is a list of YAML config directories or unified files
    """
    config_paths = get_config_paths(config_paths)
    if not config_paths:
        return {}
    data = load_yaml(config_paths)
    return load_data(data)
