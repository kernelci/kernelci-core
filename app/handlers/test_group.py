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

"""The RequestHandler for /test/group URLs."""

import bson
import datetime
import types

import handlers.response as hresponse
import handlers.test_base as htbase
import models
import models.test_group as mtgroup
import taskqueue.tasks.test as taskq
import utils
import utils.db


# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
class TestGroupHandler(htbase.TestBaseHandler):
    """The test group request handler."""

    def __init__(self, application, request, **kwargs):
        super(TestGroupHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.TEST_GROUP_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.TEST_GROUP_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        group_id = kwargs.get("id", None)

        if group_id:
            response.status_code = 400
            response.reason = "To update a test group, use a PUT request"
        else:
            # TODO: double check the token with its lab name, we need to make
            # sure people are sending test reports with a token lab with the
            # correct lab name value.
            group_json = kwargs.get("json_obj", None)
            group_pop = group_json.pop
            group_get = group_json.get

            # Remove the test_cases from the JSON and pass it as is.
            cases_list = group_pop(models.TEST_CASES_KEY, [])

            group_name = group_get(models.NAME_KEY)
            # TODO: move name validation into the initial json validation.
            if utils.valid_test_name(group_name):
                # Make sure the *_id values passed are valid.
                ret_val, error = self._check_references(
                    group_get(models.BUILD_ID_KEY, None),
                    group_get(models.JOB_ID_KEY, None)
                )

                if ret_val == 200:
                    test_group = \
                        mtgroup.TestGroupDocument.from_json(group_json)
                    test_group.created_on = datetime.datetime.now(
                        tz=bson.tz_util.utc)

                    ret_val, group_id = utils.db.save(
                        self.db, test_group, manipulate=True)

                    if ret_val == 201:
                        response.status_code = ret_val
                        response.result = {models.ID_KEY: group_id}
                        response.reason = (
                            "Test group '%s' created" %
                            group_name)
                        response.headers = {
                            "Location": "/test/group/%s" % str(group_id)}

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

                        # Complete the update of the test group and import
                        # everything else.
                        if all([cases_list]):
                            self._import_group_and_cases(
                                group_json, group_id, cases_list, group_name)
                        else:
                            # Just update the test group document.
                            taskq.complete_test_group_import.apply_async(
                                [
                                    group_json,
                                    group_id,
                                    group_name,
                                    self.settings["dboptions"]
                                ]
                            )
                    else:
                        response.status_code = ret_val
                        response.reason = (
                            "Error saving test group '%s'" % group_name)
                else:
                    response.status_code = 400
                    response.reason = error
            else:
                response.status_code = 400
                response.reason = "Test group name not valid"

        return response

    def _import_group_and_cases(
            self, group_json, group_id, tests_list, group_name):
        """Call the async task to update the test group and import test cases.

        Just a thin wrapper around the real task call.

        :param group_json: The test group JSON object.
        :type group_json: dict
        :param group_id: The ID of the test group as saved in the database.
        :type group_id: bson.objectid.ObjectId
        :param tests_list: The list of tests to import.
        :type tests_list: list
        :param group_name: The name of the test group.
        :type group_name: str
        """
        taskq.complete_test_group_import.apply_async(
            [
                group_json,
                group_id,
                group_name,
                self.settings["dboptions"], self.settings["mailoptions"]
            ],
            link=taskq.import_test_cases_from_test_group.s(
                group_id,
                group_name,
                tests_list,
                self.settings["dboptions"], self.settings["mailoptions"]
            )
        )

    def _put(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        update_doc = kwargs.get("json_obj")
        doc_id = kwargs.get("id")

        try:
            group_id = bson.objectid.ObjectId(doc_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"
        else:
            if utils.db.find_one2(self.collection, group_id):
                # TODO: handle case where job_id or build_id is updated.
                update_val = utils.db.update(
                    self.collection, {models.ID_KEY: group_id}, update_doc)

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
            group_id = bson.objectid.ObjectId(doc_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"
        else:
            if utils.db.find_one2(self.collection, group_id):
                response.status_code = utils.db.delete(
                    self.collection, group_id)

                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % doc_id

                    test_case_canc = utils.db.delete(
                        self.db[models.TEST_CASE_COLLECTION],
                        {models.TEST_GROUP_ID_KEY: group_id})

                    if test_case_canc != 200:
                        response.errors = (
                            "Error deleting test cases with "
                            "test_group_id '%s'" % doc_id)
                else:
                    response.reason = "Error deleting resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)

        return response

    # TODO: consider caching results here as well.
    def _check_references(self, build_id, job_id):
        """Check that the provided IDs are valid.

        :param build_id: The ID of the associated build.
        :type build_id: string
        :param job_id: The ID of the associated job.
        :type job_id: string
        """
        ret_val = 200
        error = None

        try:
            build_oid = bson.objectid.ObjectId(build_id)
            if job_id:
                job_oid = bson.objectid.ObjectId(job_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            ret_val = 400
            error = "Invalid value passed for build_id or job_id"
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

        return ret_val, error
