# Copyright (C) 2020 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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

import importlib


class Database:
    """KernelCI database interface"""

    def __init__(self, config, token=None):
        """Handle KernelCI data and communicate with any supported database

        This abstract class provides an interface for exchanging data with a
        database using an arbitrary implementation.  It also provides common
        logic when applicable, to handle KernelCI data in a generic way.

        *config* is the database configuration object
        *token* is an authentication token for the database
        """
        self._config = config
        self._token = token

    def submit(self, data, path=None, verbose=False):
        """Submit arbitrary data to the database

        Primitive method to send some data to the database.

        *data* is the payload to send to the database
        *path* is to identify the part of the API to use to send the data
        *verbose* is to print more information
        """
        raise NotImplementedError("Database.submit() must be implemented")

    @property
    def config(self):
        """Database configuration"""
        return self._config


def get_db(config, token=None):
    m = importlib.import_module('.'.join(['kernelci', 'data', config.db_type]))
    db = m.get_db(config, token)
    return db
