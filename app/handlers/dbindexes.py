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


def ensure_indexes(database):
    """Ensure that mongodb indexes exists, if not create them.

    This should be called at server startup.

    :param database: The database connection.
    """
    _ensure_job_indexes(database)
    _ensure_boot_indexes(database)
    _ensure_boot_regressions_indexes(database)
    _ensure_build_indexes(database)
    _ensure_token_indexes(database)
    _ensure_lab_indexes(database)
    _ensure_bisect_indexes(database)
    _ensure_error_logs_indexes(database)
    _ensure_stats_indexes(database)
    _ensure_reports_indexes(database)
    _ensure_test_group_indexes(database)
    _ensure_test_case_indexes(database)


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
    collection.ensure_index(
        [
            (models.MACH_KEY, pymongo.ASCENDING),
            (models.BOARD_KEY, pymongo.ASCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.MACH_KEY, pymongo.ASCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.CREATED_KEY, pymongo.DESCENDING),
            (models.ID_KEY, pymongo.DESCENDING),
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.DESCENDING),
            (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
            (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
            (models.BOARD_KEY, pymongo.ASCENDING),
            (models.LAB_NAME_KEY, pymongo.ASCENDING),
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.GIT_BRANCH_KEY, pymongo.ASCENDING)
        ],
        background=True
    )


def _ensure_build_indexes(database):
    """Ensure indexes exists for the 'build' collection.

    :param database: The database connection.
    """
    collection = database[models.BUILD_COLLECTION]

    collection.ensure_index(
        [
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [
            (models.CREATED_KEY, pymongo.DESCENDING),
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.DESCENDING),
            (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
            (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
            (models.STATUS_KEY, pymongo.ASCENDING),
            (models.GIT_BRANCH_KEY, pymongo.ASCENDING),
            (models.ID_KEY, pymongo.ASCENDING)
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
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.DESCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    # This is used in the aggregation pipeline.
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.DESCENDING),
            (models.GIT_BRANCH_KEY, pymongo.ASCENDING),
            (models.GIT_URL_KEY, pymongo.ASCENDING),
            (models.GIT_COMMIT_KEY, pymongo.ASCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING),
            (models.ID_KEY, pymongo.DESCENDING)
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
    collection.ensure_index(
        models.CREATED_KEY,
        expireAfterSeconds=1209600,
        background=True
    )


def _ensure_error_logs_indexes(database):
    """Ensure indexes exists for the 'error_logs' collection.

    :param database: The database connection.
    """
    collection = database[models.ERROR_LOGS_COLLECTION]
    collection.ensure_index(
        [(models.BUILD_ID_KEY, pymongo.DESCENDING)],
        background=True
    )


def _ensure_stats_indexes(database):
    """Ensure indexes exists for the 'daily_stats' collection.

    :param database: The database connection.
    """
    collection = database[models.DAILY_STATS_COLLECTION]
    collection.ensure_index(
        [(models.CREATED_KEY, pymongo.DESCENDING)], background=True)


def _ensure_boot_regressions_indexes(database):
    """Ensure indexes exist on the boot regression collection.

    :param database: The database connection.
    """
    collection = database[models.BOOT_REGRESSIONS_COLLECTION]
    collection.ensure_index(
        [
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.DESCENDING),
            (models.CREATED_KEY, pymongo.DESCENDING)
        ],
        background=True
    )
    collection.ensure_index(
        [(models.JOB_ID_KEY, pymongo.DESCENDING)], background=True)

    # The index collection.
    collection = database[models.BOOT_REGRESSIONS_BY_BOOT_COLLECTION]
    collection.ensure_index(
        [(models.BOOT_ID_KEY, pymongo.DESCENDING)], background=True)
    collection.ensure_index(
        [(models.CREATED_KEY, pymongo.DESCENDING)], background=True)


def _ensure_reports_indexes(database):
    """Ensure indexes exist on the report collection.

    :param database: The database connection.
    """
    collection = database[models.REPORT_COLLECTION]
    collection.ensure_index(
        models.CREATED_KEY,
        expireAfterSeconds=604800,
        background=True
    )


def _ensure_test_group_indexes(database):
    """Ensure indexes exist on the test_group collection.

    :param database: The database connection.
    """
    collection = database[models.TEST_GROUP_COLLECTION]
    collection.ensure_index(
        [
            (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
            (models.BOARD_KEY, pymongo.ASCENDING),
            (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
            (models.GIT_BRANCH_KEY, pymongo.ASCENDING),
            (models.JOB_KEY, pymongo.ASCENDING),
            (models.KERNEL_KEY, pymongo.ASCENDING),
            (models.LAB_NAME_KEY, pymongo.ASCENDING),
            (models.NAME_KEY, pymongo.ASCENDING),
        ],
        background=True
    )


def _ensure_test_case_indexes(database):
    """Ensure indexes exist on the test_case collection.

    :param database: The database connection.
    """
    collection = database[models.TEST_CASE_COLLECTION]
    collection.ensure_index(
        [(models.TEST_GROUP_ID_KEY, pymongo.ASCENDING)], background=True)
