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
    models.BUILD_ID_KEY,
    models.DEFCONFIG_KEY,
    models.GIT_BRANCH_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.LAB_NAME_KEY,
    models.STATUS_KEY
]

BOOT_SORT = [(models.CREATED_KEY, pymongo.DESCENDING)]


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
    defconfig_full = start_doc_get(models.DEFCONFIG_FULL_KEY) or defconfig
    created_on = start_doc_get(models.CREATED_KEY)
    arch = start_doc_get(models.ARCHITECTURE_KEY)
    lab_name = start_doc_get(models.LAB_NAME_KEY)

    bisect_doc = mbisect.BootBisectDocument(obj_id)
    bisect_doc.boot_id = obj_id
    bisect_doc.version = "1.0"
    bisect_doc.job = job
    bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
    bisect_doc.build_id = start_doc_get(models.BUILD_ID_KEY, None)
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
        models.CREATED_KEY: {"$lt": created_on},
        models.GIT_BRANCH_KEY: start_doc_get(models.GIT_BRANCH_KEY)
    }

    # The function to apply to each boot document to find its build
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
    # passed is found, and combine them with their build document.
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

    if start_doc and isinstance(start_doc, types.DictionaryType):
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

    if start_doc and isinstance(start_doc, types.DictionaryType):
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
            arch = start_doc_get(models.ARCHITECTURE_KEY)
            lab_name = start_doc_get(models.LAB_NAME_KEY)

            bisect_doc = mbisect.BootBisectDocument(obj_id)
            bisect_doc.compare_to = compare_to
            bisect_doc.version = "1.0"
            bisect_doc.job = job
            bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
            bisect_doc.build_id = start_doc_get(models.BUILD_ID_KEY, None)
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
                models.GIT_BRANCH_KEY: start_doc_get(models.GIT_BRANCH_KEY),
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


def create_boot_bisect(good, bad, db_options):
    """Create a boot bisection document or find existing matching one

    :param good: Passing boot data
    :type good: dict
    :param bad: Failing boot data
    :type bad: dict
    :param db_options: The options for the database connection.
    :type db_options: dictionary
    :return The BootBisectDocument instance.
    """
    database = utils.db.get_db_connection(db_options)
    good_commit, bad_commit = (b[models.GIT_COMMIT_KEY] for b in (good, bad))
    spec = {x: bad[x] for x in [
        models.LAB_NAME_KEY,
        models.DEVICE_TYPE_KEY,
        models.ARCHITECTURE_KEY,
        models.DEFCONFIG_FULL_KEY,
    ]}
    spec.update({
        models.BISECT_GOOD_COMMIT_KEY: good_commit,
        models.BISECT_BAD_COMMIT_KEY: bad_commit,
    })
    doc = utils.db.find_one2(database[models.BISECT_COLLECTION], spec)
    if doc:
        return doc
    bad_boot_id = bson.objectid.ObjectId(bad["_id"])
    doc = mbisect.BootBisectDocument(bad_boot_id)
    doc.boot_id = bad_boot_id
    doc.version = "1.0"
    doc.job = bad[models.JOB_KEY]
    doc.job_id = bad[models.JOB_ID_KEY]
    doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    doc.bisect_data = [bad, good]
    doc.good_commit = good_commit
    doc.good_commit_url = good[models.GIT_URL_KEY]
    doc.good_commit_date = good[models.CREATED_KEY]
    doc.bad_commit = bad_commit
    doc.bad_commit_url = bad[models.GIT_URL_KEY]
    doc.bad_commit_date = bad[models.CREATED_KEY]
    doc.kernel = bad[models.KERNEL_KEY]
    doc.git_branch = bad[models.GIT_BRANCH_KEY]
    doc.git_url = bad[models.GIT_URL_KEY]
    doc.arch = bad[models.ARCHITECTURE_KEY]
    doc.defconfig = bad[models.DEFCONFIG_KEY]
    doc.defconfig_full = bad[models.DEFCONFIG_FULL_KEY]
    doc.compiler = bad[models.COMPILER_KEY]
    doc.compiler_version = bad[models.COMPILER_VERSION_KEY]
    doc.build_environment = bad[models.BUILD_ENVIRONMENT_KEY]
    doc.build_id = bad[models.BUILD_ID_KEY]
    doc.lab_name = bad[models.LAB_NAME_KEY]
    doc.device_type = bad[models.DEVICE_TYPE_KEY]
    bcommon.save_bisect_doc(database, doc, bad_boot_id)
    return doc.to_dict()


def update_results(data, db_options):
    """Update boot bisection results

    :param data: Meta-data of the boot bisection including results
    :type data: dict
    :param db_options: The options for the database connection.
    :type db_options: dictionary
    :return A numeric value with the result status.
    """
    database = utils.db.get_db_connection(db_options)
    specs = {x: data[x] for x in [
        models.TYPE_KEY,
        models.ARCHITECTURE_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.BUILD_ENVIRONMENT_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.GIT_BRANCH_KEY,
        models.LAB_NAME_KEY,
        models.DEVICE_TYPE_KEY,
        models.BISECT_GOOD_COMMIT_KEY,
        models.BISECT_BAD_COMMIT_KEY,
    ]}
    update = {k: data[k] for k in [
        models.BISECT_GOOD_SUMMARY_KEY,
        models.BISECT_BAD_SUMMARY_KEY,
        models.BISECT_FOUND_SUMMARY_KEY,
        models.BISECT_LOG_KEY,
        models.BISECT_CHECKS_KEY,
    ]}
    return utils.db.update(database[models.BISECT_COLLECTION], specs, update)
