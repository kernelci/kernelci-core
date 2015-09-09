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

BUILD_DOC_SORT = [(models.DEFCONFIG_KEY, pymongo.ASCENDING)]


# pylint: disable=too-many-instance-attributes
class CompareJob(object):
    """An object to store data for baseline and comparison documents.

    This is used to give a common data structure during the comparison.
    It will provide access to the common values found in all the provided docs
    as well as views on locally indexed values.
    """
    def __init__(self, docs):
        self.docs = docs
        self.empty = True

        self.created_on = None
        self.git_branch = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.job = None
        self.job_id = None
        self.kernel = None

        self._total_docs = None
        self.failed = 0
        self.passed = 0
        self.other = 0

        # Hold the indexes of the docs. Keys are, respectively:
        # (defconfig, defconfig_full, arch)
        # (defconfig, defconfig_full, arch, status)
        self.defconfig = {}
        self.defconfig_status = {}
        # Internally used: store the data that can be used to identify the job.
        self._job_data = None

        self._setup_data()

    @property
    def total_docs(self):
        """Total number of docs."""
        if self._total_docs is None:
            self._total_docs = len(self.docs)
        return self._total_docs

    @property
    def build_counts(self):
        """A 3-tuples with the passed, failed and other status build counts."""
        return (self.passed, self.failed, self.other)

    @property
    def defconfig_view(self):
        """The view-like object on the indexed defconfigs."""
        return self.defconfig.viewkeys()

    @property
    def defconfig_status_view(self):
        """The view-like object on the indexes defconfigs-status."""
        return self.defconfig_status.viewkeys()

    @property
    def job_data(self):
        """The necessary data to identify a document.

        This is the data that can be used to uniquely identify a single build.
        :return A dictionary.
        """
        if all([self._job_data is None, not self.empty]):
            self._job_data = {
                models.BUILD_COUNTS_KEY: self.build_counts,
                models.CREATED_KEY: self.created_on,
                models.GIT_BRANCH_KEY: self.git_branch,
                models.GIT_COMMIT_KEY: self.git_commit,
                models.GIT_DESCRIBE_KEY: self.git_describe,
                models.GIT_URL_KEY: self.git_url,
                models.JOB_ID_KEY: self.job_id,
                models.JOB_KEY: self.job,
                models.KERNEL_KEY: self.kernel,
                models.TOTAL_BUILDS_KEY: self.total_docs
            }
        return self._job_data

    def _setup_data(self):
        """Setup the necessary data."""
        if self.docs:
            self.empty = False
            b_doc = self.docs[0]
            d_get = b_doc.get

            self.created_on = d_get(models.CREATED_KEY, None)
            self.git_branch = d_get(models.GIT_BRANCH_KEY, None)
            self.git_commit = d_get(models.GIT_COMMIT_KEY, None)
            self.git_describe = d_get(models.GIT_DESCRIBE_KEY, None)
            self.git_url = d_get(models.GIT_URL_KEY, None)
            self.job = d_get(models.JOB_KEY, None)
            self.job_id = d_get(models.JOB_ID_KEY, None)
            self.kernel = d_get(models.KERNEL_KEY, None)

            for idx, doc in enumerate(self.docs):
                d_get = doc.get
                defconfig = d_get(models.DEFCONFIG_KEY, None)
                defconfig_full = d_get(models.DEFCONFIG_FULL_KEY, None)
                status = d_get(models.STATUS_KEY, None)
                arch = d_get(models.ARCHITECTURE_KEY, None)

                if status == models.PASS_STATUS:
                    self.passed += 1
                elif status == models.FAIL_STATUS:
                    self.failed += 1
                else:
                    self.other += 1

                self.defconfig[(defconfig, defconfig_full, arch)] = idx
                self.defconfig_status[
                    (defconfig, defconfig_full, arch, status)] = idx


def _n_way_compare(baseline, compare_to):
    """Perform a n-way comparison with the baseline point and all the others.

    :param baseline: The comparison starting point.
    :type baseline: CompareJob
    :param compare_to: List of CompareJob documents to compare against.
    :type compare_to: list
    :return A 2-tuples of two lists: the first list contains dictionaries with
    the data of the compared docs. The second list contains the actual delta
    results: a 2-tuples of lists.
    """
    # Hold the data necessary to identify each compared document.
    compared_data = []
    # Hold the delta results: a list of 2-tuples.
    # The 2-tuple contain:
    # 0. A 3-tuple: (defconfig, defconfig_full, arch)
    # 1. A list with the build statuses.
    delta_result = []

    if compare_to:
        # Hold the sets of (defconfig, defconfig_full, status) keys for
        # each parsed document.
        other_sets = []
        # Hold all the symmetric differences we find in the parsed docs.
        other_diff = set()
        # Locally store baseline attributes.
        base_defconf_view = baseline.defconfig_view
        base_status_view = set(baseline.defconfig_status_view)

        # Go through the documents we have to compare against, and for each
        # extract the necessary data and compare it with baseline.
        # We perform a symmetric difference finding all the docs that are
        # either in baseline or the compared one, but not in both.
        comp_set = None
        for obj in compare_to:
            compared_data.append(obj.job_data)
            comp_set = set(obj.defconfig_status_view)
            other_sets.append(comp_set)
            other_diff.update(base_status_view.symmetric_difference(comp_set))

        other_diff = list(other_diff)

        # Store the elements we parse, so that we do not go through them more
        # than once.
        parsed_el = []
        parsed_append = parsed_el.append

        # Hold the real result of the comparison.
        # Keys are (defconfig, defconfig_full, arch), values are a list of the
        # build status with None in case of missing build.
        delta_data = {}

        for diff in other_diff:
            d_el = (diff[0], diff[1], diff[2])

            if d_el not in parsed_el:
                parsed_append(d_el)
                delta_data[d_el] = []
                status_append = delta_data[d_el].append

                # First consider the baseline point that should always be
                # at position 0.
                if d_el in base_defconf_view:
                    doc = baseline.docs[baseline.defconfig[d_el]]
                    status_append(
                        (doc[models.STATUS_KEY], doc[models.ID_KEY]))
                else:
                    status_append(None)

                # Then go through all the compared objects.
                for obj in compare_to:
                    if d_el in obj.defconfig_view:
                        doc = obj.docs[obj.defconfig[d_el]]
                        status_append(
                            (doc[models.STATUS_KEY], doc[models.ID_KEY]))
                    else:
                        status_append(None)

        delta_result = delta_data.items()
        delta_result.sort()

    return compared_data, delta_result


def _search_docs(compare_to, database, errors):
    """Search for the docs to compare against.

    :param compare_to: The list of JSON objects to search.
    :type compare_to: list
    :param database: The database connection.
    :param errors: Where errors should be added.
    :type errors: dict
    :return A list of CompareJob documents.
    """
    compare_obj = []
    for comp_spec in compare_to:
        is_valid, _ = utils.validator.is_valid_json(
            comp_spec, models.compare.JOB_DELTA_COMPARE_TO_VALID_KEYS)

        if is_valid:
            utils.update_id_fields(comp_spec)

            docs = utils.db.find(
                database[models.BUILD_COLLECTION],
                0,
                0,
                spec=comp_spec, fields=BUILD_DOC_FIELDS, sort=BUILD_DOC_SORT
            )
            if docs:
                d_docs = docs.clone()
                compare_obj.append(CompareJob([x for x in d_docs]))
                docs.close()
            else:
                ADD_ERR(
                    errors,
                    404,
                    "No compare documents found for: %s" % str(comp_spec)
                )
        else:
            ADD_ERR(
                errors,
                400,
                "Invalid data found in compare section for: %s" %
                str(comp_spec)
            )

    return compare_obj


# pylint: disable=too-many-locals
# pylint: disable=too-many-arguments
def _search_and_compare(
        job_id, job, kernel, compare_to, errors, db_options):
    """Search the docs in the database and compare them.

    :param job_id: The ID of the job to start the comparison.
    :type job_id: str
    :param job: The job value of the documents to start the comparison.
    :type job: str
    :param kernel: The kernel value of the documents to start the comparison.
    :type kernel: str
    :param compare_to: The list of JSON documents to search to compair against.
    :type compare_to: list
    :param errors: The data structure that will hold the errors.
    :type errors: dict
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return A 2-tuple: The status code (201 Created), the comparison result.
    """
    status_code = 201
    result = []
    spec = None
    base_docs = None
    database = None

    # Default to local database connection.
    if not db_options:
        db_options = {}

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
            b_docs = base_docs.clone()
            baseline = CompareJob([x for x in b_docs])
            base_docs.close()

            result_data = {}
            result_data[models.BASELINE_KEY] = baseline.job_data

            compare_docs = _search_docs(compare_to, database, errors)
            compared_data, delta_data = _n_way_compare(baseline, compare_docs)

            result_data[models.COMPARE_TO_KEY] = compared_data
            result_data[models.DELTA_RESULT_KEY] = delta_data

            result = [result_data]
        else:
            status_code = 404
            ADD_ERR(errors, 404, "No data found as comparison starting point")
    else:
        status_code = 400
        ADD_ERR(errors, 400, "No valid data found for the starting point")

    return status_code, result


def execute_job_delta(json_obj, db_options=None):
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

    if db_options is None:
        db_options = {}

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
        # Need to make sure that when the compare_to dictionaries come in they
        # have determined sorting, or we might have POST requests with exactly
        # the same data that create multiple identical results (due to the
        # fact that the keys order in a dictionary is not deterministic).
        # Create a list of ordered tuples.
        compare_to_sorted = []
        comp_extend = compare_to_sorted.extend
        for element in compare_to:
            element_items = element.items()
            element_items.sort()
            comp_extend(element_items)
        json_obj[models.COMPARE_TO_KEY] = compare_to_sorted

        # First search for any saved results.
        saved = utils.compare.common.search_saved_delta_doc(
            json_obj, models.JOB_DELTA_COLLECTION, db_options)

        if saved:
            result, doc_id = saved[0], saved[1]
        else:
            status_code, result = _search_and_compare(
                job_id, job, kernel, compare_to, errors, db_options)

            if status_code == 201:
                doc_id = utils.compare.common.save_delta_doc(
                    json_obj,
                    result, models.JOB_DELTA_COLLECTION, db_options)

    return status_code, result, doc_id, errors
