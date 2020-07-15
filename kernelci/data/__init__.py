# Copyright (C) 2020 Collabora Limited
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

import importlib


class Database:

    def __init__(self, config, token=None):
        self._config = config
        self._token = token

    def submit(self, data):
        raise NotImplementedError("Database.submit() must be implemented")

    @property
    def config(self):
        return self._config


def get_db(config, token=None):
    m = importlib.import_module('.'.join(['kernelci', 'data', config.db_type]))
    db = m.get_db(config, token)
    return db
