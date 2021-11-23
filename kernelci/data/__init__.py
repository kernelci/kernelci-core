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
import json


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

    @property
    def config(self):
        """Database configuration"""
        return self._config

    def submit(self, data, verbose=False):
        """Submit arbitrary data to the database

        Primitive method to send some data to the database.

        *data* is a dictionary with the data to send to the database
        *verbose* is to print more information
        """
        raise NotImplementedError("Database.submit() must be implemented")

    def submit_build(self, meta, verbose=False):
        """Submit meta-data for a kernel build

        Alternative entry point to submit the kernel build meta-data from a
        build.Metadata object.

        *meta* is a kernelci.build.Metadata object
        *verbose* is to print more information
        """
        raise NotImplementedError("Database.submit_build() not implemented")

    def submit_test(self, results, verbose=False):
        """Submit test results

        Alternative entry point to submit test results.

        *results* is a dictionary with the test results data
        *verbose* is to print more information
        """
        raise NotImplementedError("Database.submit_test() not implemented")

    def _print_http_error(self, http_error, verbose=False):
        print(http_error)
        if verbose:
            errors = json.loads(http_error.response.content).get("errors", [])
            for err in errors:
                print(err)


def get_db(config, token=None):
    m = importlib.import_module('.'.join(['kernelci', 'data', config.db_type]))
    db = m.get_db(config, token)
    return db
