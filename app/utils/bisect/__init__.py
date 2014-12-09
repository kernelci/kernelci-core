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

"""All the bisect operations that the app can perform."""

try:
    import simplejson as json
except ImportError:
    import json

import bson
import bson.json_util
import copy
import datetime
import pymongo
import types

import models
import models.bisect as mbisect
import utils
import utils.db

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

BOOT_DEFCONFIG_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_KEY,
    models.GIT_BRANCH_KEY,
    models.GIT_COMMIT_KEY,
    models.GIT_DESCRIBE_KEY,
    models.GIT_URL_KEY,
    models.STATUS_KEY
]

BOOT_SORT = [(models.CREATED_KEY, pymongo.DESCENDING)]

DEFCONFIG_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_KEY,
    models.GIT_COMMIT_KEY,
    models.GIT_DESCRIBE_KEY,
    models.GIT_URL_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.STATUS_KEY
]

DEFCONFIG_SORT = [(models.CREATED_KEY, pymongo.DESCENDING)]


def _combine_defconfig_values(boot_doc, db_options):
    """Combine the boot document values with their own defconfing.

    It returns a dictionary whose structure is a combination
    of the values from the boot document and its associated defconfing.

    :param boot_doc: The boot document to retrieve the defconfig of.
    :type boot_doc: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A dictionary.
    """
    database = utils.db.get_db_connection(db_options)

    boot_doc_get = boot_doc.get

    job = boot_doc_get(models.JOB_KEY)
    kernel = boot_doc_get(models.KERNEL_KEY)
    defconfig = boot_doc_get(models.DEFCONFIG_KEY)
    defconfig_full = boot_doc_get(models.DEFCONFIG_FULL_KEY)
    defconfig_id = boot_doc_get(models.DEFCONFIG_ID_KEY, None)
    job_id = boot_doc_get(models.JOB_ID_KEY, None)

    combined_values = {
        models.BISECT_BOOT_CREATED_KEY: boot_doc_get(models.CREATED_KEY),
        models.BISECT_BOOT_METADATA_KEY: boot_doc_get(models.METADATA_KEY),
        models.BISECT_BOOT_STATUS_KEY: boot_doc_get(models.STATUS_KEY),
        models.BISECT_DEFCONFIG_ARCHITECTURE_KEY: "",
        models.BISECT_DEFCONFIG_CREATED_KEY: "",
        models.BISECT_DEFCONFIG_STATUS_KEY: "",
        models.DEFCONFIG_FULL_KEY: defconfig_full,
        models.DEFCONFIG_ID_KEY: defconfig_id,
        models.DEFCONFIG_KEY: defconfig,
        models.DIRNAME_KEY: "",
        models.GIT_BRANCH_KEY: "",
        models.GIT_COMMIT_KEY: "",
        models.GIT_DESCRIBE_KEY: "",
        models.GIT_URL_KEY: "",
        models.JOB_ID_KEY: job_id,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel
    }

    if defconfig_id:
        defconf_doc = utils.db.find_one(
            database[models.DEFCONFIG_COLLECTION],
            [defconfig_id],
            fields=BOOT_DEFCONFIG_SEARCH_FIELDS
        )
    else:
        defconfig_name = job + "-" + kernel + "-" + defconfig
        defconf_doc = utils.db.find_one(
            database[models.DEFCONFIG_COLLECTION],
            [defconfig_name],
            field=models.NAME_KEY,
            fields=BOOT_DEFCONFIG_SEARCH_FIELDS
        )

    if defconf_doc:
        defconf_doc_get = defconf_doc.get
        combined_values[models.DIRNAME_KEY] = defconf_doc_get(
            models.DIRNAME_KEY)
        combined_values[models.BISECT_DEFCONFIG_CREATED_KEY] = \
            defconf_doc_get(models.CREATED_KEY)
        combined_values[models.BISECT_DEFCONFIG_ARCHITECTURE_KEY] = \
            defconf_doc_get(models.ARCHITECTURE_KEY)
        combined_values[models.BISECT_DEFCONFIG_STATUS_KEY] = \
            defconf_doc_get(models.STATUS_KEY)
        combined_values[models.GIT_URL_KEY] = defconf_doc_get(
            models.GIT_URL_KEY, None)
        combined_values[models.GIT_BRANCH_KEY] = defconf_doc_get(
            models.GIT_BRANCH_KEY, None)
        combined_values[models.GIT_COMMIT_KEY] = defconf_doc_get(
            models.GIT_COMMIT_KEY, None)
        combined_values[models.GIT_DESCRIBE_KEY] = defconf_doc_get(
            models.GIT_DESCRIBE_KEY, None)

    return combined_values


def execute_boot_bisection(doc_id, db_options, fields=None):
    """Perform a bisect-like on the provided boot report.

    It searches all the previous boot reports starting from the provided one
    until it finds one whose boot passed. After that, it looks for all the
    defconfig reports and combines the value into a single data structure.

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
    start_doc = utils.db.find_one(
        database[models.BOOT_COLLECTION], [obj_id], fields=BOOT_SEARCH_FIELDS
    )

    if all([start_doc, isinstance(start_doc, types.DictionaryType)]):
        start_doc_get = start_doc.get

        if start_doc_get(models.STATUS_KEY) == models.PASS_STATUS:
            code = 400
            result = None
        else:
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
            bisect_doc.version = "1.0"
            bisect_doc.job = job
            bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
            bisect_doc.defconfig_id = start_doc_get(
                models.DEFCONFIG_ID_KEY, None)
            bisect_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
            bisect_doc.board = board

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
            func = _combine_defconfig_values

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
                        for doc in _get_docs_until_pass(all_prev_docs)
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

            return_code, saved_id = utils.db.save(
                database, bisect_doc, manipulate=True)
            if return_code == 201:
                bisect_doc.id = saved_id
            else:
                utils.LOG.error("Error saving bisect data %s", doc_id)

            bisect_doc = _update_doc_fields(bisect_doc, fields)
            result = [
                json.loads(
                    json.dumps(
                        bisect_doc,
                        default=bson.json_util.default,
                        ensure_ascii=False
                    )
                )
            ]
    else:
        code = 404
        result = None

    return code, result


def execute_defconfig_bisection(doc_id, db_options, fields=None):
    """Calculate bisect data for the provided defconfig report.

    It searches all the previous defconfig built starting from the provided one
    until it finds one that passed. After that, it combines the value into a
    single data structure.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return A numeric value for the result status and a list of dictionaries.
    """
    database = utils.db.get_db_connection(db_options)
    result = []
    code = 200

    obj_id = bson.objectid.ObjectId(doc_id)
    start_doc = utils.db.find_one(
        database[models.DEFCONFIG_COLLECTION],
        [obj_id], fields=DEFCONFIG_SEARCH_FIELDS
    )

    if all([start_doc, isinstance(start_doc, types.DictionaryType)]):
        start_doc_get = start_doc.get

        if start_doc_get(models.STATUS_KEY) == models.PASS_STATUS:
            code = 400
            result = None
        else:
            bisect_doc = mbisect.DefconfigBisectDocument(obj_id)
            bisect_doc.version = "1.0"
            bisect_doc.arch = start_doc_get(models.ARCHITECTURE_KEY, None)
            bisect_doc.job = start_doc_get(models.JOB_KEY, None)
            bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
            bisect_doc.defconfig_id = start_doc_get(models.ID_KEY)
            bisect_doc.defconfig = start_doc_get(models.DEFCONFIG_KEY, None)
            bisect_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
            bisect_doc.bad_commit_date = start_doc_get(models.CREATED_KEY)
            bisect_doc.bad_commit = start_doc_get(models.GIT_COMMIT_KEY)
            bisect_doc.bad_commit_url = start_doc_get(models.GIT_URL_KEY)

            spec = {
                models.ARCHITECTURE_KEY: start_doc_get(
                    models.ARCHITECTURE_KEY),
                models.DEFCONFIG_FULL_KEY: start_doc_get(
                    models.DEFCONFIG_FULL_KEY),
                models.DEFCONFIG_KEY: start_doc_get(models.DEFCONFIG_KEY),
                models.JOB_KEY: start_doc_get(models.JOB_KEY),
            }

            all_valid_docs = [start_doc]

            # Search for the first passed defconfig so that we can limit the
            # next search. Doing this to cut down search and load time on
            # mongodb side: there are a lot of defconfig documents to search
            # for and the mongodb Cursor can get quite big.
            # Tweak the spec to search for PASS status and limit also the
            # result found: we are only interested in the first found one.
            # Need to use copy.deepcoy here since for some strange reasons,
            # just adding and removing the keys from the spec is not working
            # as expected.
            pass_spec = copy.deepcopy(spec)
            pass_spec[models.STATUS_KEY] = models.PASS_STATUS
            # Only interested in older builds.
            pass_spec[models.CREATED_KEY] = \
                {"$lt": start_doc_get(models.CREATED_KEY)}

            passed_builds = utils.db.find(
                database[models.DEFCONFIG_COLLECTION],
                10,
                0,
                spec=pass_spec,
                fields=DEFCONFIG_SEARCH_FIELDS,
                sort=DEFCONFIG_SORT
            )

            # In case we have a passed doc, tweak the spec to search between
            # the valid dates.
            passed_build = None
            if passed_builds.count() > 0:
                passed_build = passed_builds[0]

                if passed_build.get(models.STATUS_KEY) != models.PASS_STATUS:
                    utils.LOG.warn(
                        "First result found is not a passed build for '%s'",
                        obj_id
                    )
                    for doc in passed_builds:
                        if doc.get(models.STATUS_KEY) == models.PASS_STATUS:
                            passed_build = doc
                            break

                spec[models.CREATED_KEY] = {
                    "$gte": passed_build.get(models.CREATED_KEY),
                    "$lt": start_doc_get(models.CREATED_KEY)
                }
            else:
                utils.LOG.warn("No passed build found for '%s'", obj_id)
                spec[models.CREATED_KEY] = {
                    "$lt": start_doc_get(models.CREATED_KEY)
                }

            all_prev_docs = utils.db.find(
                database[models.DEFCONFIG_COLLECTION],
                0,
                0,
                spec=spec,
                fields=DEFCONFIG_SEARCH_FIELDS,
                sort=DEFCONFIG_SORT
            )

            if all_prev_docs:
                all_valid_docs.extend(
                    [
                        doc for doc in _get_docs_until_pass(all_prev_docs)
                    ]
                )

                if all([passed_build, all_valid_docs[-1] != passed_build]):
                    all_valid_docs.append(passed_build)

                # The last doc should be the good one, in case it is, add the
                # values to the bisect_doc.
                good_doc = all_valid_docs[-1]
                if (good_doc[models.STATUS_KEY] == models.PASS_STATUS):
                    good_doc_get = good_doc.get
                    bisect_doc.good_commit = good_doc_get(
                        models.GIT_COMMIT_KEY)
                    bisect_doc.good_commit_url = good_doc_get(
                        models.GIT_URL_KEY)
                    bisect_doc.good_commit_date = good_doc_get(
                        models.CREATED_KEY)

            # Store everything in the bisect data.
            bisect_doc.bisect_data = all_valid_docs

            return_code, saved_id = utils.db.save(
                database, bisect_doc, manipulate=True)
            if return_code == 201:
                bisect_doc.id = saved_id
            else:
                utils.LOG.error("Error saving bisect data %s", doc_id)

            bisect_doc = _update_doc_fields(bisect_doc, fields)
            result = [
                json.loads(
                    json.dumps(
                        bisect_doc,
                        default=bson.json_util.default,
                        ensure_ascii=False
                    )
                )
            ]
    else:
        code = 404
        result = None

    return code, result


def _update_doc_fields(bisect_doc, fields):
    """Update the bisect document based on the provided fields.

    Return the dictionary view of the bisect document with the fields as
    specified in the `fields` data structure passed.

    A `fields` data structure can be a list or dictionary.

    :param bisect_doc: The document to update.
    :type bisect_doc: BisectDocument
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The BisectDocument as a dict calling it `to_dict()` method.
    """
    if fields:
        if isinstance(fields, list):
            bisect_doc = bisect_doc.to_dict()
            to_remove = list(bisect_doc.viewkeys() - set(fields))
            for field in to_remove:
                if field == models.ID_KEY:
                    continue
                else:
                    bisect_doc.pop(field)
        elif isinstance(fields, types.DictionaryType):
            y_fields = [
                field for field, val in fields.iteritems() if val
            ]
            n_fields = list(fields.viewkeys() - set(y_fields))

            bisect_doc = _update_doc_fields(bisect_doc, y_fields)
            for field in n_fields:
                bisect_doc.pop(field, None)
        else:
            bisect_doc = bisect_doc.to_dict()
    else:
        bisect_doc = bisect_doc.to_dict()
    return bisect_doc


def _get_docs_until_pass(doc_list):
    """Iterate through the docs until one that passed is found.

    Yield all documents until one that passed is found, returning it as well
    and breaking the loop.

    :param doc_list: A list of documents (`BaseDocument`) as dictionaries.
    :type doc_list: list
    """
    for doc in doc_list:
        if doc[models.STATUS_KEY] == models.PASS_STATUS:
            yield doc
            break
        yield doc
