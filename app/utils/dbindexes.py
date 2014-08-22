# Copyright (C) 2014 Linaro Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Make sure indexes are created at startup."""

from pymongo import (
    ASCENDING,
    DESCENDING,
)

from models import (
    CREATED_KEY,
    DB_NAME,
    STATUS_KEY
)
from models.job import JOB_COLLECTION
from models.boot import BOOT_COLLECTION
from models.defconfig import DEFCONFIG_COLLECTION


def ensure_indexes(client):
    """Ensure that mongodb indexes exists, if not create them.

    This should be called at server startup.

    :param client: The mongodb client used to access the database.
    """
    database = client[DB_NAME]

    _ensure_job_indexes(database)
    _ensure_boot_indexes(database)
    _ensure_defconfig_indexes(database)


def _ensure_job_indexes(database):
    """Ensure indexes exists for the 'job' collection.

    :param database: The database connection.
    """
    database[JOB_COLLECTION].ensure_index(
        [(CREATED_KEY, DESCENDING)], background=True
    )


def _ensure_boot_indexes(database):
    """Ensure indexes exists for the 'boot' collection.

    :param database: The database connection.
    """
    database[BOOT_COLLECTION].ensure_index(
        [(CREATED_KEY, DESCENDING)], background=True
    )


def _ensure_defconfig_indexes(database):
    """Ensure indexes exists for the 'defconfig' collection.

    :param database: The database connection.
    """
    collection = database[DEFCONFIG_COLLECTION]

    collection.ensure_index([(CREATED_KEY, DESCENDING)], background=True)
    collection.ensure_index([(STATUS_KEY, ASCENDING)], background=True)
