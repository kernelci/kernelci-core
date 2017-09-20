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

"""The RequestHandler for /test/suite URLs."""

import bson
import datetime
import types

import handlers.response as hresponse
import handlers.test_base as htbase
import models
import models.test_suite as mtsuite
import taskqueue.tasks.test as taskq
import utils
import utils.db


# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
class TestSuiteHandler(htbase.TestBaseHandler):
    """The test suite request handler."""

    def __init__(self, application, request, **kwargs):
        super(TestSuiteHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.TEST_SUITE_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.TEST_SUITE_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        suite_id = kwargs.get("id", None)

        if suite_id:
            response.status_code = 400
            response.reason = "To update a test suite, use a PUT request"
        else:
            # TODO: double check the token with its lab name, we need to make
            # sure people are sending test reports with a token lab with the
            # correct lab name value. Check the boot handler.
            suite_json = kwargs.get("json_obj", None)
            suite_pop = suite_json.pop
            suite_get = suite_json.get

            # Remove the test_set and test_case from the JSON and pass them
            # as is.
            sets_list = suite_pop(models.TEST_SET_KEY, [])
            cases_list = suite_pop(models.TEST_CASE_KEY, [])

            suite_name = suite_get(models.NAME_KEY)
            # TODO: move name validation into the initial json validation.
            if utils.valid_test_name(suite_name):
                # Make sure the *_id values passed are valid.
                ret_val, error = self._check_references(
                    suite_get(models.BUILD_ID_KEY, None),
                    suite_get(models.JOB_ID_KEY, None),
                    suite_get(models.BOOT_ID_KEY, None)
                )

                if ret_val == 200:
                    test_suite = \
                        mtsuite.TestSuiteDocument.from_json(suite_json)
                    test_suite.created_on = datetime.datetime.now(
                        tz=bson.tz_util.utc)

                    ret_val, suite_id = utils.db.save(
                        self.db, test_suite, manipulate=True)

                    if ret_val == 201:
                        response.status_code = ret_val
                        response.result = {models.ID_KEY: suite_id}
                        response.reason = (
                            "Test suite '%s' created" %
                            suite_name)
                        response.headers = {
                            "Location": "/test/suite/%s" % str(suite_id)}

                        if sets_list:
                            if isinstance(sets_list, types.ListType):
                                response.status_code = 202
                                response.messages = (
                                    "Test sets will be parsed and imported")
                            else:
                                sets_list = []
                                response.errors = (
                                    "Test sets are not wrapped in a list; "
                                    "they will not be imported")

                        if cases_list:
                            if isinstance(cases_list, types.ListType):
                                response.status_code = 202
                                response.messages = (
                                    "Test cases will be parsed and imported")
                            else:
                                cases_list = []
                                response.errors = (
                                    "Test cases are not wrapped in a "
                                    "list; they will not be imported")

                        # Complete the update of the test suite and import
                        # everything else.
                        if all([cases_list, sets_list]):
                            self._import_suite_with_sets_and_cases(
                                suite_json,
                                suite_id, sets_list, cases_list, suite_name)
                        elif all([cases_list, not sets_list]):
                            self._import_suite_and_cases(
                                suite_json, suite_id, cases_list, suite_name)
                        elif all([not cases_list, sets_list]):
                            self._import_suite_and_sets(
                                suite_json, suite_id, sets_list, suite_name)
                        else:
                            # Just update the test suite document.
                            taskq.complete_test_suite_import.apply_async(
                                [
                                    suite_json,
                                    suite_id,
                                    suite_name,
                                    self.settings["dboptions"]
                                ]
                            )
                    else:
                        response.status_code = ret_val
                        response.reason = (
                            "Error saving test suite '%s'" % suite_name)
                else:
                    response.status_code = 400
                    response.reason = error
            else:
                response.status_code = 400
                response.reason = "Test suite name not valid"

        return response

    # pylint: disable=too-many-arguments
    def _import_suite_with_sets_and_cases(
            self,
            suite_json, suite_id, sets_list, cases_list, suite_name):
        """Update the test suite and import test sets and cases.

        Just a thin wrapper around the real task call.

        :param suite_json: The test suite JSON object.
        :type suite_json: dict
        :param suite_id: The ID of the test suite as saved in the database.
        :type suite_id: bson.objectid.ObjectId
        :param sets_list: The list of test sets to import.
        :type sets_list: list
        :param cases_list: The list of test cases to import.
        :type cases_list: list
        :param suite_name: The name of the test suite.
        :type suite_name: str
        """
        taskq.complete_test_suite_import.apply_async(
            [
                suite_json,
                suite_id,
                suite_name,
                self.settings["dboptions"], self.settings["mailoptions"]
            ],
            link=[
                taskq.import_test_sets_from_test_suite.s(
                    suite_id,
                    suite_name,
                    sets_list,
                    self.settings["dboptions"], self.settings["mailoptions"]
                ),
                taskq.import_test_cases_from_test_suite.s(
                    suite_id,
                    suite_name,
                    cases_list,
                    self.settings["dboptions"], self.settings["mailoptions"]
                )
            ]
        )

    def _import_suite_and_cases(
            self, suite_json, suite_id, tests_list, suite_name):
        """Call the async task to update the test suite and import test cases.

        Just a thin wrapper around the real task call.

        :param suite_json: The test suite JSON object.
        :type suite_json: dict
        :param suite_id: The ID of the test suite as saved in the database.
        :type suite_id: bson.objectid.ObjectId
        :param tests_list: The list of tests to import.
        :type tests_list: list
        :param suite_name: The name of the test suite.
        :type suite_name: str
        """
        taskq.complete_test_suite_import.apply_async(
            [
                suite_json,
                suite_id,
                suite_name,
                self.settings["dboptions"], self.settings["mailoptions"]
            ],
            link=taskq.import_test_cases_from_test_suite.s(
                suite_id,
                suite_name,
                tests_list,
                self.settings["dboptions"], self.settings["mailoptions"]
            )
        )

    def _import_suite_and_sets(
            self, suite_json, suite_id, tests_list, suite_name):
        """Call the async task to update the test suite and import test sets.

        Just a thin wrapper around the real task call.

        :param suite_json: The test suite JSON object.
        :type suite_json: dict
        :param suite_id: The ID of the test suite as saved in the database.
        :type suite_id: bson.objectid.ObjectId
        :param tests_list: The list of tests to import.
        :type tests_list: list
        :param suite_name: The name of the test suite.
        :type suite_name: str
        """
        taskq.complete_test_suite_import.apply_async(
            [
                suite_json,
                suite_id,
                suite_name,
                self.settings["dboptions"], self.settings["mailoptions"]
            ],
            link=taskq.import_test_sets_from_test_suite.s(
                suite_id,
                suite_name,
                tests_list,
                self.settings["dboptions"], self.settings["mailoptions"]
            )
        )

    def _put(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        update_doc = kwargs.get("json_obj")
        doc_id = kwargs.get("id")

        try:
            suite_id = bson.objectid.ObjectId(doc_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"
        else:
            if utils.db.find_one2(self.collection, suite_id):
                # TODO: handle case where boot_id, job_id or build_id
                # is updated.
                update_val = utils.db.update(
                    self.collection, {models.ID_KEY: suite_id}, update_doc)

                if update_val == 200:
                    response.reason = "Resource '%s' updated" % doc_id
                else:
                    response.status_code = update_val
                    response.reason = "Error updating resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)

        return response

    def _delete(self, doc_id, **kwargs):
        response = hresponse.HandlerResponse()

        try:
            suite_id = bson.objectid.ObjectId(doc_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"
        else:
            if utils.db.find_one2(self.collection, suite_id):
                response.status_code = utils.db.delete(
                    self.collection, suite_id)

                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % doc_id

                    test_set_canc = utils.db.delete(
                        self.db[models.TEST_SET_COLLECTION],
                        {models.TEST_SUITE_ID_KEY: suite_id})

                    test_case_canc = utils.db.delete(
                        self.db[models.TEST_CASE_COLLECTION],
                        {models.TEST_SUITE_ID_KEY: suite_id})

                    if test_case_canc != 200:
                        response.errors = (
                            "Error deleting test cases with "
                            "test_suite_id '%s'" % doc_id)
                    if test_set_canc != 200:
                        response.errors = (
                            "Error deleting test sets with "
                            "test_suite_id '%s'" % doc_id)
                else:
                    response.reason = "Error deleting resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)

        return response

    # TODO: consider caching results here as well.
    def _check_references(self, build_id, job_id, boot_id):
        """Check that the provided IDs are valid.

        :param build_id: The ID of the associated build.
        :type build_id: string
        :param job_id: The ID of the associated job.
        :type job_id: string
        :param boot_id: The ID of the associated boot report.
        :type boot_id: string
        """
        ret_val = 200
        error = None

        try:
            build_oid = bson.objectid.ObjectId(build_id)
            if job_id:
                job_oid = bson.objectid.ObjectId(job_id)
            if boot_id:
                boot_oid = bson.objectid.ObjectId(boot_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            ret_val = 400
            error = "Invalid value passed for build_id, job_id, or boot_id"
        else:
            build_doc = utils.db.find_one2(
                self.db[models.BUILD_COLLECTION], build_oid, [models.ID_KEY])
            if not build_doc:
                ret_val = 400
                error = "Build document with ID '%s' not found" % build_id
            else:
                if job_id:
                    job_doc = utils.db.find_one2(
                        self.db[models.JOB_COLLECTION],
                        job_oid, [models.ID_KEY])
                    if not job_doc:
                        ret_val = 400
                        error = "Job document with ID '%s' not found" % job_id

                if all([boot_id, error is None]):
                    boot_doc = utils.db.find_one2(
                        self.db[models.BOOT_COLLECTION],
                        boot_oid, [models.ID_KEY])
                    if not boot_doc:
                        ret_val = 400
                        error = (
                            "Boot document with ID '%s' not found" % boot_id)

        return ret_val, error
