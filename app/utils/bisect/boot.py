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

"""All boot bisect operations."""

import bson
import bson.json_util
import datetime
import pymongo
import types

import models
import models.bisect as mbisect
import utils
import utils.db
import utils.bisect.common as bcommon

BOOT_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_ID_KEY,
    models.DEFCONFIG_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.LAB_NAME_KEY,
    models.STATUS_KEY
]

BOOT_SORT = [(models.CREATED_KEY, pymongo.DESCENDING)]


def execute_boot_bisection(doc_id, db_options, fields=None):
    """Perform a bisect-like on the provided boot report.

    It searches all the previous boot reports starting from the provided one
    until it finds one whose boot passed. After that, it looks for all the
    build reports and combines the value into a single data structure.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return A numeric value for the result status and a list dictionaries.
    """
    database = utils.db.get_db_connection(db_options)
    result = []
    code = 200

    obj_id = bson.objectid.ObjectId(doc_id)
    start_doc = utils.db.find_one2(
        database[models.BOOT_COLLECTION], obj_id, fields=BOOT_SEARCH_FIELDS)

    if all([start_doc, isinstance(start_doc, types.DictionaryType)]):
        start_doc_get = start_doc.get

        if start_doc_get(models.STATUS_KEY) == models.PASS_STATUS:
            code = 400
            result = None
        else:
            bisect_doc = _find_boot_bisect_data(
                obj_id, start_doc, database, db_options)
            bcommon.save_bisect_doc(database, bisect_doc, doc_id)

            bisect_doc = bcommon.update_doc_fields(bisect_doc, fields)
            result = [bisect_doc]
    else:
        code = 404
        result = None

    return code, result


# pylint: disable=too-many-locals
def _find_boot_bisect_data(obj_id, start_doc, database, db_options):
    """Execute the real bisect logic.

    This is where the BisectDocument is created and returned.

    :param obj_id: The `bson.objectid.ObjectId` of the starting point.
    :type obj_id: bson.objectid.ObjectId
    :param start_doc: The starting document.
    :type start_doc: dictionary
    :param database: The connection to the database.
    :param db_options: The options for the database connection.
    :type db_options: dictionary
    :return A BisectDocument instance.
    """
    start_doc_get = start_doc.get

    board = start_doc_get(models.BOARD_KEY)
    job = start_doc_get(models.JOB_KEY)
    defconfig = start_doc_get(models.DEFCONFIG_KEY)
    defconfig_full = start_doc_get(
        models.DEFCONFIG_FULL_KEY) or defconfig
    created_on = start_doc_get(models.CREATED_KEY)
    arch = start_doc_get(
        models.ARCHITECTURE_KEY) or models.ARM_ARCHITECTURE_KEY
    lab_name = start_doc_get(models.LAB_NAME_KEY)

    bisect_doc = mbisect.BootBisectDocument(obj_id)
    bisect_doc.boot_id = obj_id
    bisect_doc.version = "1.0"
    bisect_doc.job = job
    bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
    bisect_doc.defconfig_id = start_doc_get(
        models.DEFCONFIG_ID_KEY, None)
    bisect_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    bisect_doc.board = board
    bisect_doc.arch = arch
    bisect_doc.defconfig = defconfig
    bisect_doc.defconfig_full = defconfig_full

    spec = {
        models.LAB_NAME_KEY: lab_name,
        models.BOARD_KEY: board,
        models.DEFCONFIG_KEY: defconfig,
        models.DEFCONFIG_FULL_KEY: defconfig_full,
        models.JOB_KEY: start_doc_get(models.JOB_KEY),
        models.ARCHITECTURE_KEY: arch,
        models.CREATED_KEY: {"$lt": created_on}
    }

    # The function to apply to each boot document to find its defconfig
    # one and combine the values.
    func = bcommon.combine_defconfig_values

    bad_doc = func(start_doc, db_options)
    bad_doc_get = bad_doc.get

    bisect_doc.bad_commit_date = bad_doc_get(
        models.BISECT_DEFCONFIG_CREATED_KEY)
    bisect_doc.bad_commit = bad_doc_get(models.GIT_COMMIT_KEY)
    bisect_doc.bad_commit_url = bad_doc_get(models.GIT_URL_KEY)

    all_valid_docs = [bad_doc]

    # Search through all the previous boot reports, until one that
    # passed is found, and combine them with their defconfig document.
    all_prev_docs = utils.db.find(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SORT
    )

    if all_prev_docs:
        all_valid_docs.extend(
            [
                func(doc, db_options)
                for doc in bcommon.get_docs_until_pass(all_prev_docs)
            ]
        )
        # The last doc should be the good one, in case it is, add the
        # values to the bisect_doc.
        good_doc = all_valid_docs[-1]
        if (good_doc[models.BISECT_BOOT_STATUS_KEY] ==
                models.PASS_STATUS):
            good_doc_get = good_doc.get
            bisect_doc.good_commit = good_doc_get(
                models.GIT_COMMIT_KEY)
            bisect_doc.good_commit_url = good_doc_get(
                models.GIT_URL_KEY)
            bisect_doc.good_commit_date = good_doc_get(
                models.BISECT_DEFCONFIG_CREATED_KEY)

    # Store everything in the bisect_data list of the bisect_doc.
    bisect_doc.bisect_data = all_valid_docs
    return bisect_doc


# pylint: disable=invalid-name
def execute_boot_bisection_compared_to(
        doc_id, compare_to, db_options, fields=None):
    """Execute a bisect for one tree compared to another one.

    :param doc_id: The ID of the boot report we want compared.
    :type doc_id: string
    :param compare_to: The tree name to compare against.
    :type compare_to: string
    :param db_options: The options for the database connection.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return A numeric value for the result status and a list dictionaries.
    """
    database = utils.db.get_db_connection(db_options)
    result = []
    code = 200

    obj_id = bson.objectid.ObjectId(doc_id)
    start_doc = utils.db.find_one2(
        database[models.BOOT_COLLECTION], obj_id, fields=BOOT_SEARCH_FIELDS)

    if all([start_doc, isinstance(start_doc, types.DictionaryType)]):
        start_doc_get = start_doc.get

        if start_doc_get(models.STATUS_KEY) == models.PASS_STATUS:
            code = 400
            result = None
        else:
            # TODO: we need to know the baseline tree commit in order not to
            # search too much in the past.
            end_date, limit = bcommon.search_previous_bisect(
                database,
                {models.BOOT_ID_KEY: obj_id},
                models.BISECT_BOOT_CREATED_KEY
            )

            board = start_doc_get(models.BOARD_KEY)
            job = start_doc_get(models.JOB_KEY)
            defconfig = start_doc_get(models.DEFCONFIG_KEY)
            defconfig_full = start_doc_get(
                models.DEFCONFIG_FULL_KEY) or defconfig
            created_on = start_doc_get(models.CREATED_KEY)
            arch = start_doc_get(
                models.ARCHITECTURE_KEY) or models.ARM_ARCHITECTURE_KEY
            lab_name = start_doc_get(models.LAB_NAME_KEY)

            bisect_doc = mbisect.BootBisectDocument(obj_id)
            bisect_doc.compare_to = compare_to
            bisect_doc.version = "1.0"
            bisect_doc.job = job
            bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
            bisect_doc.defconfig_id = start_doc_get(
                models.DEFCONFIG_ID_KEY, None)
            bisect_doc.boot_id = obj_id
            bisect_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
            bisect_doc.board = board
            bisect_doc.defconfig_full = defconfig_full
            bisect_doc.defconfig = defconfig
            bisect_doc.arch = arch

            if end_date:
                date_range = {
                    "$lt": created_on,
                    "$gte": end_date
                }
            else:
                date_range = {"$lt": created_on}

            spec = {
                models.LAB_NAME_KEY: lab_name,
                models.BOARD_KEY: board,
                models.DEFCONFIG_KEY: defconfig,
                models.DEFCONFIG_FULL_KEY: defconfig_full,
                models.JOB_KEY: compare_to,
                models.ARCHITECTURE_KEY: arch,
                models.CREATED_KEY: date_range
            }
            prev_docs = utils.db.find(
                database[models.BOOT_COLLECTION],
                limit,
                0,
                spec=spec,
                fields=BOOT_SEARCH_FIELDS,
                sort=BOOT_SORT)

            all_valid_docs = []
            if prev_docs:
                # The function to apply to each boot document to find its
                # defconfig one and combine the values.
                func = bcommon.combine_defconfig_values

                all_valid_docs.extend(
                    [
                        func(doc, db_options) for doc in prev_docs
                    ]
                )

            bisect_doc.bisect_data = all_valid_docs
            bcommon.save_bisect_doc(database, bisect_doc, doc_id)

            bisect_doc = bcommon.update_doc_fields(bisect_doc, fields)
            result = [bisect_doc]
    else:
        code = 404
        result = None

    return code, result
