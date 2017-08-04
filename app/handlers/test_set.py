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

"""The RequestHandler for /test/set URLs."""

import bson
import datetime
import types

import handlers.response as hresponse
import handlers.test_base as htbase
import models
import models.test_set as mtset
import taskqueue.tasks.test as taskq
import utils.db


# pylint: disable=too-many-public-methods
class TestSetHandler(htbase.TestBaseHandler):
    """The test set request handler."""

    def __init__(self, application, request, **kwargs):
        super(TestSetHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.TEST_SET_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.TEST_SET_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        set_id = kwargs.get("id", None)

        if set_id:
            response.status_code = 400
            response.reason = "To update a test set, use a PUT request"
        else:
            test_set_json = kwargs.get("json_obj", None)
            j_pop = test_set_json.pop
            j_get = test_set_json.get
            test_cases = j_pop(models.TEST_CASE_KEY, [])
            suite_id = j_get(models.TEST_SUITE_ID_KEY)
            set_name = j_get(models.NAME_KEY)

            suite_oid, suite_name, err_msg = \
                self._check_and_get_test_suite(suite_id)

            if suite_oid:
                try:
                    test_set = mtset.TestSetDocument.from_json(test_set_json)
                    test_set.created_on = datetime.datetime.now(
                        tz=bson.tz_util.utc)
                    test_set.test_suite_id = suite_oid

                    ret_val, doc_id = utils.db.save(
                        self.db, test_set, manipulate=True)
                    response.status_code = ret_val

                    if ret_val == 201:
                        response.result = {models.ID_KEY: doc_id}
                        response.reason = "Test set '%s' created" % set_name
                        response.headers = {
                            "Location": "/test/set/%s" % str(doc_id)}

                        # Update test_suite add test set ID
                        self._update_test_suite_add_test_set_id(
                            doc_id, suite_oid, suite_name)

                        if test_cases:
                            if isinstance(test_cases, types.ListType):
                                response.status_code = 202
                                response.messages = (
                                    "Test cases will be parsed and "
                                    "imported")
                                self._import_test_cases(
                                    test_cases, doc_id, suite_oid, suite_name)
                            else:
                                response.errors = (
                                    "Test cases are not wrapped in a "
                                    "list; they will not be imported")
                    else:
                        response.reason = (
                            "Error saving test set '%s'" % set_name)
                except ValueError, ex:
                    error = "Wrong field value in JSON data"
                    self.log.error(error)
                    self.log.exception(ex)
                    response.status_code = 400
                    response.reason = error
                    response.errors = ex.message
            else:
                self.log.error(
                    "Test suite '%s' not found or not valid ID", suite_id)
                response.status_code = 400
                response.reason = err_msg

        return response

    def _update_test_suite_add_test_set_id(
            self, set_oid, suite_oid, suite_name):
        """Execute the async task to add the test set ID onto the test suite.

        :param set_oid: The ID of the test set.
        :type set_oid: bson.objectid.ObjectId
        :param suite_oid: The ID of the test suite.
        :type suite_oid: bson.objectid.ObjectId
        :param suite_name: The name of the test suite.
        :type suite_name: str
        """
        taskq.update_test_suite_add_test_set_id.apply_async(
            [
                set_oid,
                suite_oid,
                suite_name,
            ]
        )

    def _import_test_cases(self, test_cases, set_oid, suite_oid, suite_name):
        """Execute the async task to import the test cases.

        :param test_cases: The test cases list to import.
        :type test_cases: list
        :param set_oid: The ID of the test set.
        :type set_oid: bson.objectid.ObjectId
        :param suite_oid: The ID of the test suite.
        :type suite_oid: bson.objectid.ObjectId
        :param suite_name: The name of the test suite.
        :type suite_name: str
        """
        taskq.import_test_cases_from_test_set.apply_async(
            [
                test_cases,
                suite_oid,
                suite_name,
                set_oid,
                self.settings["dboptions"], self.settings["mailoptions"]
            ]
        )

    def _delete(self, doc_id, **kwargs):
        response = hresponse.HandlerResponse()

        try:
            set_id = bson.objectid.ObjectId(doc_id)
            if utils.db.find_one2(self.collection, set_id):
                response.status_code = utils.db.delete(self.collection, set_id)

                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % doc_id

                    ret_val = utils.db.delete(
                        self.db[models.TEST_CASE_COLLECTION],
                        {models.TEST_SET_ID_KEY: set_id})

                    if ret_val != 200:
                        response.errors = (
                            "Error deleting test cases with "
                            "test_set_id '%s'" % doc_id)

                    # Remove test set reference from test_suite collection.
                    ret_val = utils.db.update(
                        self.db[models.TEST_SUITE_COLLECTION],
                        {models.TEST_SET_KEY: set_id},
                        {models.TEST_SET_KEY: [set_id]},
                        operation="$pullAll"
                    )
                    if ret_val != 200:
                        response.errors = \
                            "Error removing test set reference from test suite"
                else:
                    response.reason = "Error deleting resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"

        return response

    def _put(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        update_doc = kwargs.get("json_obj")
        doc_id = kwargs.get("id")

        try:
            set_id = bson.objectid.ObjectId(doc_id)
            if utils.db.find_one2(self.collection, set_id):
                update_val = utils.db.update(
                    self.collection, {models.ID_KEY: set_id}, update_doc)

                if update_val == 200:
                    response.reason = "Resource '%s' updated" % doc_id
                else:
                    response.status_code = update_val
                    response.reason = "Error updating resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"
        return response
