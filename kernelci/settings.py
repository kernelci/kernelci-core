#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI TOML Settings

KernelCI relies on TOML Settings to provide a way to store secrets and default
values for command line arguments.  Each user typically has their own TOML
settings file for particular use-cases.
"""

import os

import toml


class Settings:
    """KernelCI TOML Settings

    This class loads settings from a TOML file and provides utilities to
    retrieve values from it.  The `path` argument passed when creating the
    object can be used to load an arbitrary TOML file.  Otherwise, the default
    paths are:

        kernelci.toml in the current directory
        ~/.config/kernelci/kernelci.toml
        /etc/kernelci/kernelci.toml
    """

    def __init__(self, path: str = None):
        if path is not None:
            if not os.path.exists(path):
                raise FileNotFoundError(path)
        else:
            default_paths = [
                'kernelci.toml',
                os.path.expanduser('~/.config/kernelci/kernelci.toml'),
                '/etc/kernelci/kernelci.toml',
            ]
            for default_path in default_paths:
                if os.path.exists(default_path):
                    path = default_path
                    break
        self._path = path
        self._settings = toml.load(path) if path else {}

    @property
    def path(self):
        """Path to the loaded TOML settings file"""
        return self._path

    def get_raw(self, *args):
        """Get a settings value from an arbitrary series of keys

        The *args are a tuple of strings for the path, e.g. ('foo', 'bar',
        'baz') will look for a foo.bar.baz value or baz within [foo.bar] etc.

        This method returns None if the value or any element of the path
        doesn't exist.  If the last element is not a single value but a group
        then it will return a dictionary with the settings for that group.
        """
        data = self._settings
        for arg in args:
            if not isinstance(data, dict):
                data = None
            if data is None:
                break
            data = data.get(arg)
        return data

    def get(self, *args):
        """Get a settings value using inheritance

        Unlike .get_raw() which directly returns what is found from the TOML
        settings, the .get() method will try and find a key within the path as
        a default value.  For example, if kci.api is defined in TOML but not
        kci.node.api, when trying to retrieve ('kci', 'node', 'api') it will
        return the value found in ('kci', 'api') as a default value.  This
        allows setting values across all the sub-commands.

        This method will also always return a final value and never a group
        dictionary like .get_raw().  If the requested value is not found and no
        parent section with the same final key has been found, then this method
        returns None.
        """
        if len(args) < 1:
            return None
        key = args[-1]
        data = self._settings
        value = data.get(key)
        for arg in args:
            if not isinstance(data, dict):
                data = None
            if data is None:
                break
            value = data.get(key, value)
            data = data.get(arg)
        return value


class Secrets:
    """Helper class to find the secrets section in the settings

    This provides a way to access secrets using attributes and sub-group names.
    For example, when trying to access secrets.api.token, the value of "api"
    provided when creating the object will be used to look up the matching
    section e.g. "kci.api.local.token" if --api=local.

    The `config_args` is a dictionary with the key-value pairs used to find
    sub-gropus, for example {'api': 'local'} which is typically loaded from
    command-line arguments.

    The default location in the TOML settings for secrets is in [kci.secrets],
    so the `root` path to this is ('kci', 'secrets').
    """

    class Group:  # pylint: disable=too-few-public-methods
        """Helper class to find a key within a group"""
        def __init__(self, group: dict = None):
            self._group = group or {}

        def __getattr__(self, key: str):
            return self._group.get(key)

    def __init__(self, settings: Settings, config_args: dict = None,
                 root: tuple = None):
        self._settings = settings
        self._config_args = config_args or {}
        self._root = root or ()

    def __getattr__(self, section: str):
        name = self._config_args.get(section)
        raw_group = self._settings.get_raw(*self._root, section, name)
        return self.Group(raw_group)

    @property
    def root(self):
        """Get the rootpath for the TOML group containing secrets"""
        return self._root
