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
