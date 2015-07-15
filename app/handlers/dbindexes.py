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

import pymongo

import models


def ensure_indexes(client, db_options):
    """Ensure that mongodb indexes exists, if not create them.

    This should be called at server startup.

    :param client: The mongodb client used to access the database.
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    db_user = db_options["dbuser"]
    db_pwd = db_options["dbpassword"]

    database = client[models.DB_NAME]
    if all([db_user, db_pwd]):
        database.authenticate(db_user, password=db_pwd)

    _ensure_job_indexes(database)
    _ensure_boot_indexes(database)
    _ensure_defconfig_indexes(database)
    _ensure_token_indexes(database)
    _ensure_lab_indexes(database)
    _ensure_bisect_indexes(database)
    _ensure_error_logs_indexes(database)


def _ensure_job_indexes(database):
    """Ensure indexes exists for the 'job' collection.

    :param database: The database connection.
    """
    collection = database[models.JOB_COLLECTION]
    collection.ensure_index(
        [
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.KERNEL_KEY, pymongo.ASCENDING)
        ],
        background=True
    )


def _ensure_boot_indexes(database):
    """Ensure indexes exists for the 'boot' collection.

    :param database: The database connection.
    """
    collection = database[models.BOOT_COLLECTION]
    collection.ensure_index(
        [
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.ASCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.ASCENDING)
        ],
        background=True
    )


def _ensure_defconfig_indexes(database):
    """Ensure indexes exists for the 'defconfig' collection.

    :param database: The database connection.
    """
    collection = database[models.DEFCONFIG_COLLECTION]

    collection.ensure_index(
        [
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.ASCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.KERNEL_KEY, pymongo.ASCENDING)
        ],
        background=True
    )


def _ensure_token_indexes(database):
    """Ensure indexes exists for the 'token' collection.

    :param database: The database connection.
    """
    collection = database[models.TOKEN_COLLECTION]

    collection.ensure_index(
        [(models.TOKEN_KEY, pymongo.DESCENDING)], background=True
    )


def _ensure_lab_indexes(database):
    """Ensure indexes exists for the 'lab' collection.

    :param database: The database connection.
    """
    collection = database[models.LAB_COLLECTION]

    collection.ensure_index(
        [
            (models.NAME_KEY, pymongo.ASCENDING),
            (models.TOKEN_KEY, pymongo.ASCENDING)
        ],
        background=True
    )


def _ensure_bisect_indexes(database):
    """Ensure indexes exists for the 'bisect' collection.

    :param database: The database connection.
    """
    collection = database[models.BISECT_COLLECTION]

    collection.ensure_index(
        [(models.NAME_KEY, pymongo.DESCENDING)],
        background=True
    )


def _ensure_error_logs_indexes(database):
    """Ensure indexes exists for the 'error_logs' collection.

    :param database: The database connection.
    """
    collection = database[models.ERROR_LOGS_COLLECTION]
    collection.ensure_index(
        [(models.DEFCONFIG_ID_KEY, pymongo.DESCENDING)],
        background=True
    )
