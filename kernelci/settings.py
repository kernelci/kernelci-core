# Copyright (C) 2020 Collabora Limited
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

import configparser
import os.path


class Settings:
    """User Settings with CLI override."""

    def __init__(self, path, section, args):
        """A Settings object provides key/value pairs via its attributes.

        The settings are first loaded from a settings file in the using
        `configparser` module.  The attribute name is first looked up in the
        command line arguments, so they take precendence over the settings
        file.  Conversely, any command line argument can have a default value
        set in the settings file.

        *path* is the path to the config file, which by default is
               ~/.config/kernelci/kernelci.conf
        *section" is the name of the section in the settings file
        *args* is an object with command line arguments as produced by argparse
        """
        if path is None:
            path = os.path.expanduser('~/.config/kernelci/kernelci.conf')
        self._settings = configparser.ConfigParser()
        if os.path.exists(path):
            self._settings.read(path)
        self._section = section
        self._args = args

    def __getattr__(self, name):
        return self.get(name)

    @property
    def args(self):
        """The command line arguments object."""
        return self._args

    def get(self, option, as_list=False):
        """Get a settings value.

        This is an explicit call to get a settings value, which can also be
        done by accessing an object attribute i.e. `self.option`.

        *option* is the name of the settings optin to look up

        *as_list* is whether the value should be returned as a list, for
                  settings which have multiple values separated by whitespaces
                  in the settings file
        """
        value = getattr(self.args, option, None)
        if value:
            return value
        if not self._settings.has_option(self._section, option):
            return None
        value = self._settings.get(self._section, option).split()
        if not as_list and len(value) == 1:
            value = value[0]
        return value
