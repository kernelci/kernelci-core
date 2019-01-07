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

"""All build bisect operations."""

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
import utils.bisect.common as bcommon

BUILD_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_KEY,
    models.GIT_BRANCH_KEY,
    models.GIT_COMMIT_KEY,
    models.GIT_DESCRIBE_KEY,
    models.GIT_URL_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.STATUS_KEY
]

BUILD_SORT = [(models.CREATED_KEY, pymongo.DESCENDING)]


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def execute_build_bisection(doc_id, db_options, fields=None):
    """Calculate bisect data for the provided build report.

    It searches all the previous builds starting from the provided one
    until it finds one that passed. After that, it combines the value into a
    single data structure.

    :param doc_id: The build document ID.
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
        database[models.BUILD_COLLECTION],
        [obj_id],
        fields=BUILD_SEARCH_FIELDS
    )

    if start_doc and isinstance(start_doc, types.DictionaryType):
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
            bisect_doc.build_id = start_doc_get(models.ID_KEY)
            bisect_doc.defconfig = start_doc_get(models.DEFCONFIG_KEY, None)
            bisect_doc.defconfig_full = start_doc_get(
                models.DEFCONFIG_FULL_KEY, None)
            bisect_doc.git_branch = start_doc_get(models.GIT_BRANCH_KEY)
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
                models.GIT_BRANCH_KEY: start_doc_get(models.GIT_BRANCH_KEY)
            }

            all_valid_docs = [start_doc]

            # Search for the first passed build so that we can limit the
            # next search. Doing this to cut down search and load time on
            # mongodb side: there are a lot of build documents to search
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
                database[models.BUILD_COLLECTION],
                10,
                0,
                spec=pass_spec,
                fields=BUILD_SEARCH_FIELDS,
                sort=BUILD_SORT
            )

            # In case we have a passed doc, tweak the spec to search between
            # the valid dates.
            passed_build = None
            if passed_builds.count() > 0:
                passed_build = _search_passed_doc(passed_builds)

            if passed_build is not None:
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
                database[models.BUILD_COLLECTION],
                0,
                0,
                spec=spec,
                fields=BUILD_SEARCH_FIELDS,
                sort=BUILD_SORT
            )

            if all_prev_docs:
                all_valid_docs.extend(
                    [
                        doc for doc in
                        bcommon.get_docs_until_pass(all_prev_docs)
                    ]
                )

                if passed_build and all_valid_docs[-1] != passed_build:
                    all_valid_docs.append(passed_build)

                # The last doc should be the good one, in case it is, add the
                # values to the bisect_doc.
                good_doc = all_valid_docs[-1]
                if good_doc[models.STATUS_KEY] == models.PASS_STATUS:
                    good_doc_get = good_doc.get
                    bisect_doc.good_commit = good_doc_get(
                        models.GIT_COMMIT_KEY)
                    bisect_doc.good_commit_url = good_doc_get(
                        models.GIT_URL_KEY)
                    bisect_doc.good_commit_date = good_doc_get(
                        models.CREATED_KEY)

            # Store everything in the bisect data.
            bisect_doc.bisect_data = all_valid_docs
            bcommon.save_bisect_doc(database, bisect_doc, doc_id)

            bisect_doc = bcommon.update_doc_fields(bisect_doc, fields)
            result = [bisect_doc]
    else:
        code = 404
        result = None

    return code, result


def _search_passed_doc(passed_builds):
    """Search for a document with PASS status.

    :param passed_builds: The list or an iterator of docs to parse.
    :return A doc with PASS status or None.
    """
    passed_build = passed_builds[0]

    if passed_build.get(models.STATUS_KEY) != models.PASS_STATUS:
        passed_build = None
        for doc in passed_builds:
            if doc.get(models.STATUS_KEY) == models.PASS_STATUS:
                passed_build = doc
                break

    return passed_build


# pylint: disable=invalid-name
def execute_build_bisection_compared_to(
        doc_id, compare_to, db_options, fields=None):
    """Execute a bisect for one tree compared to another one.

    :param doc_id: The ID of the build report we want compared.
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
        database[models.BUILD_COLLECTION],
        obj_id, fields=BUILD_SEARCH_FIELDS)

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
                {models.BUILD_ID_KEY: obj_id},
                models.CREATED_KEY
            )

            job = start_doc_get(models.JOB_KEY)
            defconfig = start_doc_get(models.DEFCONFIG_KEY)
            defconfig_full = start_doc_get(
                models.DEFCONFIG_FULL_KEY) or defconfig
            created_on = start_doc_get(models.CREATED_KEY)
            arch = start_doc_get(models.ARCHITECTURE_KEY)
            branch = start_doc_get(models.GIT_BRANCH_KEY)

            bisect_doc = mbisect.DefconfigBisectDocument(obj_id)
            bisect_doc.compare_to = compare_to
            bisect_doc.version = "1.0"
            bisect_doc.defconfig = defconfig
            bisect_doc.defconfig_full = defconfig_full
            bisect_doc.job = job
            bisect_doc.job_id = start_doc_get(models.JOB_ID_KEY, None)
            bisect_doc.build_id = start_doc_get(models.BUILD_ID_KEY, None)
            bisect_doc.boot_id = obj_id
            bisect_doc.git_branch = branch
            bisect_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
            bisect_doc.arch = arch

            if end_date:
                date_range = {
                    "$lt": created_on,
                    "$gte": end_date
                }
            else:
                date_range = {"$lt": created_on}

            spec = {
                models.DEFCONFIG_KEY: defconfig,
                models.DEFCONFIG_FULL_KEY: defconfig_full,
                models.GIT_BRANCH_KEY: branch,
                models.JOB_KEY: compare_to,
                models.ARCHITECTURE_KEY: arch,
                models.CREATED_KEY: date_range
            }

            prev_docs = utils.db.find(
                database[models.BUILD_COLLECTION],
                limit,
                0,
                spec=spec,
                fields=BUILD_SEARCH_FIELDS,
                sort=BUILD_SORT)

            all_valid_docs = []
            if prev_docs:
                all_valid_docs.extend(prev_docs)

            # Store everything in the bisect data.
            bisect_doc.bisect_data = all_valid_docs
            bcommon.save_bisect_doc(database, bisect_doc, doc_id)

            bisect_doc = bcommon.update_doc_fields(bisect_doc, fields)
            result = [bisect_doc]
    else:
        code = 404
        result = None

    return code, result
