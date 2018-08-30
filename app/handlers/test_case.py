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

"""The RequestHandler for /test/case URLs."""

import bson

import handlers.response as hresponse
import handlers.test_base as htbase
import models
import utils.db
import utils.tests_import as tests_import


# pylint: disable=too-many-public-methods
class TestCaseHandler(htbase.TestBaseHandler):
    """The test set request handler."""

    def __init__(self, application, request, **kwargs):
        super(TestCaseHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.TEST_CASE_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.TEST_CASE_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        set_id = kwargs.get("id", None)

        if set_id:
            response.status_code = 400
            response.reason = "To update a test case, use a PUT request"
        else:
            test_case_json = kwargs.get("json_obj", None)
            j_get = test_case_json.get
            group_id = j_get(models.TEST_GROUP_ID_KEY)
            case_name = j_get(models.NAME_KEY)

            group_oid, group_name, err_msg = \
                self._check_and_get_test_group(group_id)

            if group_oid:
                ret_val, doc_id, err_msg = tests_import.import_test_case(
                    test_case_json,
                    group_oid,
                    group_name,
                    self.db, self.settings["dboptions"]
                )
                response.status_code = ret_val

                if ret_val == 201:
                    response.result = {models.ID_KEY: doc_id}
                    response.reason = "Test case '%s' created" % case_name
                    response.headers = {
                        "Location": "/test/case/%s" % str(doc_id)}
                else:
                    response.reason = "Error saving test case '%s'" % case_name
                    response.errors = err_msg
            else:
                self.log.error(
                    "Test group '%s' not found or not valid ID", group_id)
                response.status_code = 400
                response.reason = err_msg

        return response

    def _delete(self, doc_id, **kwargs):
        response = hresponse.HandlerResponse()

        try:
            case_id = bson.objectid.ObjectId(doc_id)
            if utils.db.find_one2(self.collection, case_id):
                response.status_code = utils.db.delete(
                    self.collection, case_id)

                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % doc_id

                    # Remove test case reference from the test_group collection
                    ret_val = utils.db.update(
                        self.db[models.TEST_GROUP_COLLECTION],
                        {models.TEST_CASE_KEY: case_id},
                        {models.TEST_CASE_KEY: [case_id]},
                        operation="$pullAll"
                    )
                    if ret_val != 200:
                        response.errors = (
                            "Error removing test case reference from test "
                            "group")
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
