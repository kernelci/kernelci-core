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

"""Perform job delta calculations.

Job delta calculations are performed on all the available build for a given
job ID (or job-kernel combination).
"""

import bson
import pymongo

import models
import models.compare
import utils
import utils.compare.common
import utils.db
import utils.errors
import utils.validator

ADD_ERR = utils.errors.add_error

# Fields that will be retrieved during the database lookup.
BUILD_DOC_FIELDS = [
    models.ARCHITECTURE_KEY,
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

BUILD_DOC_SORT = [(models.DEFCONFIG_KEY, pymongo.ASCENDING)]


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class BaselineJob(object):
    """The baseline job from where to start calculating the delta.

    This class is used to setup only once all the necessary data structures for
    the baseline doc when performing the delta calculations since.
    """

    def __init__(self, docs):
        self.docs = docs

        self.total_builds = len(self.docs)
        self.git_branch = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.job = None
        self.job_id = None
        self.kernel = None

        # Hold as keys tuples with (defconfig, defconfig_full, arch) and values
        # the index position in the list.
        self.baseline_defconfig = {}
        # Hold as keys tuples with (defconfig, defconfig_full, arch, status)
        # and values the index position in the list.
        self.baseline_defconfig_status = {}

        self._setup_baseline_data()

    def _setup_baseline_data(self):
        """Setup the necessary data for the baseline job."""
        b_doc = self.docs[0]
        d_get = b_doc.get

        self.job_id = d_get(models.JOB_ID_KEY, None)
        self.job = d_get(models.JOB_KEY, None)
        self.kernel = d_get(models.KERNEL_KEY, None)
        self.git_branch = d_get(models.GIT_BRANCH_KEY, None)
        self.git_url = d_get(models.GIT_URL_KEY, None)
        self.git_commit = d_get(models.GIT_COMMIT_KEY, None)
        self.git_describe = d_get(models.GIT_DESCRIBE_KEY, None)

        for idx, doc in enumerate(self.docs):
            d_get = doc.get
            defconfig = d_get(models.DEFCONFIG_KEY, None)
            defconfig_full = d_get(models.DEFCONFIG_FULL_KEY, None)
            status = d_get(models.STATUS_KEY, None)
            arch = d_get(models.ARCHITECTURE_KEY, None)

            self.baseline_defconfig[(defconfig, defconfig_full, arch)] = idx
            self.baseline_defconfig_status[
                (defconfig, defconfig_full, arch, status)] = idx


# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def _calculate_delta(baseline, to_compare):
    """Calculate the delta between multiple jobs.

    :param baseline: The baseline job document to start the delta.
    :type baseline: BaselineJob
    :param to_compare: The list of other documents to compare against. Each
    document must be a dict.
    :return A dict with the delta data structure.
    """

    def _redact_doc(doc):
        """Remove some fields from a document.

        Fields that are redundant between each documents will be removed.
        Document must be a dictionary instance.

        :param doc: The document to redact.
        :type doc: dict
        :return The redacted document.
        """
        doc_pop = doc.pop
        doc_pop(models.GIT_BRANCH_KEY, None)
        doc_pop(models.GIT_COMMIT_KEY, None)
        doc_pop(models.GIT_DESCRIBE_KEY, None)
        doc_pop(models.GIT_URL_KEY, None)
        doc_pop(models.JOB_ID_KEY, None)
        doc_pop(models.JOB_KEY, None)
        doc_pop(models.KERNEL_KEY, None)
        return doc

    # The delta data structure that will be returned.
    # It will contains a set of common values among all the compared document,
    # and a list with the comparison diff.
    delta_data = {}
    # Where the compared results will be stored, it will be a list of
    # 2-tuples. Each tuple contains the baseline doc and the compared doc if
    # they are both available, otherwise they will contain None.
    compare_result = []
    # Locally used to filter the results already analyzed.
    parsed_result = []

    to_compare = [x for x in to_compare]

    if to_compare:
        compared_defconfig = {}
        compared_defconfig_status = {}

        # Pick a 'compared' document and look up some of its values.
        # These are fields common to all documents we are parsing.
        c_doc = to_compare[0]
        doc_get = c_doc.get

        delta_data[models.GIT_BRANCH_KEY] = doc_get(
            models.GIT_BRANCH_KEY, None)
        delta_data[models.GIT_COMMIT_KEY] = doc_get(
            models.GIT_COMMIT_KEY, None)
        delta_data[models.GIT_DESCRIBE_KEY] = doc_get(
            models.GIT_DESCRIBE_KEY, None)
        delta_data[models.GIT_URL_KEY] = doc_get(models.GIT_URL_KEY, None)
        delta_data[models.JOB_ID_KEY] = doc_get(models.JOB_ID_KEY, None)
        delta_data[models.JOB_KEY] = doc_get(models.JOB_KEY, None)
        delta_data[models.KERNEL_KEY] = doc_get(models.KERNEL_KEY, None)
        delta_data[models.TOTAL_BUILDS_KEY] = len(to_compare)

        # Save often-accessed functions locally.
        append_parsed_result = parsed_result.append
        append_compare_result = compare_result.append

        for idx, doc in enumerate(to_compare):
            d_get = doc.get
            defconfig = d_get(models.DEFCONFIG_KEY, None)
            defconfig_full = d_get(models.DEFCONFIG_FULL_KEY, None)
            status = d_get(models.STATUS_KEY, None)
            arch = d_get(models.ARCHITECTURE_KEY, None)

            compared_defconfig[(defconfig, defconfig_full, arch)] = idx
            compared_defconfig_status[
                (defconfig, defconfig_full, arch, status)] = idx

        base_defconfig_view = baseline.baseline_defconfig.viewkeys()
        compared_defconfig_view = compared_defconfig.viewkeys()
        base_status_view = set(baseline.baseline_defconfig_status.viewkeys())
        compare_status_view = set(compared_defconfig_status.viewkeys())

        # Search for elements that are in the baseline but not in the compare.
        base_status_diff = base_status_view - compare_status_view
        # Search for elements that are in the compare but not in the baseline.
        compare_status_diff = compare_status_view - base_status_view
        all_diff = list(base_status_diff | compare_status_diff)

        for diff_el in all_diff:
            t_el = (diff_el[0], diff_el[1], diff_el[2])
            if t_el not in parsed_result:
                append_parsed_result(t_el)

                if all([t_el in compared_defconfig_view,
                        t_el in base_defconfig_view]):
                    append_compare_result(
                        (
                            _redact_doc(
                                baseline.docs[
                                    baseline.baseline_defconfig[t_el]]),
                            _redact_doc(to_compare[compared_defconfig[t_el]])
                        )
                    )
                elif all([t_el in base_defconfig_view,
                          t_el not in compared_defconfig_view]):
                    append_compare_result(
                        (
                            _redact_doc(
                                baseline.docs[
                                    baseline.baseline_defconfig[t_el]]),
                            None)
                        )
                elif all([t_el not in base_defconfig_view,
                          t_el in compared_defconfig_view]):
                    append_compare_result(
                        (
                            None,
                            _redact_doc(to_compare[compared_defconfig[t_el]]))
                        )
        delta_data[models.DELTA_RESULT_KEY] = compare_result
    else:
        utils.LOG.warn("No documents found to compare against")

    return delta_data


# pylint: disable=too-many-arguments
def _search_and_compare(
        job_id, job, kernel, compare_to, errors, db_options=None):
    """Search the docs in the database and compare them.

    :param job_id:
    :type job_id: str
    :param job:
    :type job: str
    :param kernel:
    :type kernel: str
    :param compare_to:
    :type compare_to: list
    :param errors:
    :type errors: dict
    :param db_options:
    :type db_options: dict
    :return A 2-tuple: The status code (200 OK), the delta result.
    """
    # Default to local database connection.
    if not db_options:
        db_options = {}

    def _search_docs_to_compare(database):
        """Yield the docs to compare against.

        :param database: The database connection.
        :return Yield each document search from the database.
        """
        for comp_spec in compare_to:
            is_valid, error = utils.validator.is_valid_json(
                comp_spec, models.compare.JOB_DELTA_COMPARE_TO_VALID_KEYS)

            if is_valid:
                utils.update_id_fields(comp_spec)

                yield utils.db.find(
                    database[models.BUILD_COLLECTION],
                    0,
                    0,
                    spec=comp_spec,
                    fields=BUILD_DOC_FIELDS, sort=BUILD_DOC_SORT
                )
            else:
                ADD_ERR(errors, 400, "Found invalid data in compare section")

    def _get_delta(baseline, database):
        """Yield the delta calculation for each documents.

        :param baseline: The baseline object to start from.
        :type baseline: BaselineJob
        :param database: The database connection.
        :return Yield each calculated delta.
        """
        for docs in _search_docs_to_compare(database):
            yield _calculate_delta(baseline, docs)

    status_code = 201
    result = []
    spec = None
    base_docs = None
    database = None

    if job_id:
        try:
            doc_id = bson.objectid.ObjectId(job_id)
            spec = {models.ID_KEY: doc_id}
        except bson.errors.InvalidId:
            status_code = 400
            ADD_ERR(errors, 400, "Provided job_id value is not valid")
    elif all([job, kernel]):
        spec = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel
        }

    if spec:
        database = utils.db.get_db_connection(db_options)
        base_docs = utils.db.find(
            database[models.BUILD_COLLECTION],
            0, 0, spec=spec, fields=BUILD_DOC_FIELDS, sort=BUILD_DOC_SORT)

        if base_docs:
            base_docs = [x for x in base_docs.clone()]
            baseline = BaselineJob(base_docs)

            result_data = {}
            result_data[models.BASELINE_KEY] = {
                models.GIT_BRANCH_KEY: baseline.git_branch,
                models.GIT_COMMIT_KEY: baseline.git_commit,
                models.GIT_DESCRIBE_KEY: baseline.git_describe,
                models.GIT_URL_KEY: baseline.git_url,
                models.JOB_ID_KEY: baseline.job_id,
                models.JOB_KEY: baseline.job,
                models.KERNEL_KEY: baseline.kernel,
                models.TOTAL_BUILDS_KEY: baseline.total_builds
            }

            result_data[models.RESULT_KEY] = [
                res for res in _get_delta(baseline, database)
                if res
            ]
            result = [result_data]
        else:
            status_code = 404
            ADD_ERR(errors, 404, "No data found as comparison starting point")

    return status_code, result


def execute_job_delta(json_obj, db_options):
    """Execute the job delta calculations.

    :param json_obj: The JSON object containing the data to start the delta.
    :type json_obj: dict
    :param db_options: The database connection options.
    :type db_options: dict
    :return A 3-tuple: The status code (200 OK), the list of result and an
    error data structure.
    """
    status_code = 200
    doc_id = None
    result = []
    errors = {}

    job_id = json_obj.get(models.JOB_ID_KEY, None)
    job = json_obj.get(models.JOB_KEY, None)
    kernel = json_obj.get(models.KERNEL_KEY, None)
    compare_to = json_obj.get(models.COMPARE_TO_KEY, [])

    if all([not job_id, (not job or not kernel)]):
        status_code = 400
        ADD_ERR(errors, 400, "Missing valid job, kernel or job_id value")
    elif not compare_to:
        status_code = 400
        ADD_ERR(errors, 400, "No data provided to compare to")
    else:
        # First search for any saved results.
        saved = utils.compare.common.search_saved_delta_doc(
            json_obj, models.JOB_DELTA_COLLECTION, db_options=db_options)

        if saved:
            result, doc_id = saved[0], saved[1]
        else:
            status_code, result = _search_and_compare(
                job_id, job, kernel, compare_to, errors, db_options=db_options)

            if status_code == 201:
                doc_id = utils.compare.common.save_delta_doc(
                    json_obj,
                    result, models.JOB_DELTA_COLLECTION, db_options=db_options
                )

    return status_code, result, doc_id, errors
