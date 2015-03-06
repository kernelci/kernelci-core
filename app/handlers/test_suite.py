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

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import models.test_suite as mtsuite
import utils.db


class TestSuiteHandler(hbase.BaseHandler):

    def __init__(self, application, request, **kwargs):
        super(TestSuiteHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return models.TEST_SUITE_COLLECTION

    @staticmethod
    def _valid_keys(method):
        return hcommon.TEST_SUITE_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return hcommon.valid_token_tests

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()
        suite_id = kwargs.get("id", None)

        if suite_id:
            response.status_code = 400
            response.reason = "To update a test suite, use a PUT request"
        else:
            test_suite_json = kwargs.get("json_obj", None)
            suite_pop = test_suite_json.pop
            test_set = suite_pop(models.TEST_SET_KEY, [])
            test_case = suite_pop(models.TEST_CASE_KEY, [])

            test_suite = mtsuite.TestSuiteDocument.from_json(test_suite_json)
            test_suite.created_on = datetime.datetime.now(tz=bson.tz_util.utc)

            ret_val, doc_id = utils.db.save(self.db, test_suite)

            if ret_val == 201:
                response.status_code = ret_val
                response.reason = (
                    "Test suite '%s' created with ID: %s" %
                    (test_suite.name, doc_id))

                if all([test_set, isinstance(test_set, types.ListType)]):
                    response.status_code = 202
                    response.messages = (
                        "Associated test sets will be parsed and imported")
                    # TODO: import async the test sets.
                    pass

                if all([test_case, isinstance(test_case, types.ListType)]):
                    response.status_code = 202
                    response.messages = (
                        "Associated test cases will be parsed and imported")
                    # TODO: import async the test cases.
                    pass
            else:
                response.status_code = 500
                response.reason = (
                    "Error saving test set '%s'" % test_suite.name)

        return response
