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

"""The base for the test related handlers."""

try:
    import simplejson as json
except ImportError:
    import json

import bson

import handlers.base as hbase
import handlers.common.token
import handlers.common.request
import handlers.response as hresponse
import models
import utils.db
import utils.validator as validator


# pylint: disable=too-many-public-methods
class TestBaseHandler(hbase.BaseHandler):
    """Base class for test related API handlers.

    This class provides methods and functions common to all the test API
    endpoint.
    """

    def __init__(self, application, request, **kwargs):
        super(TestBaseHandler, self).__init__(application, request, **kwargs)

    @staticmethod
    def _token_validation_func():
        return handlers.common.token.valid_token_tests

    def execute_put(self, *args, **kwargs):
        """Execute the PUT pre-operations."""
        response = None
        valid_token, token = self.validate_req_token("PUT")

        if valid_token:
            if kwargs.get("id", None):
                valid_request = handlers.common.request.valid_post_request(
                    self.request.headers, self.request.remote_ip)

                if valid_request == 200:
                    try:
                        json_obj = json.loads(self.request.body.decode("utf8"))

                        valid_json, j_reason = validator.is_valid_json(
                            json_obj, self._valid_keys("PUT"))
                        if valid_json:
                            kwargs["json_obj"] = json_obj
                            kwargs["reason"] = j_reason
                            kwargs["token"] = token
                            response = self._put(*args, **kwargs)
                        else:
                            response = hresponse.HandlerResponse(400)
                            if j_reason:
                                response.reason = (
                                    "Provided JSON is not valid: %s" %
                                    j_reason)
                            else:
                                response.reason = "Provided JSON is not valid"
                    except ValueError, ex:
                        self.log.exception(ex)
                        error = "No JSON data found in the PUT request"
                        self.log.error(error)
                        response = hresponse.HandlerResponse(422)
                        response.reason = error
                else:
                    response = hresponse.HandlerResponse(valid_request)
                    response.reason = (
                        "%s: %s" %
                        (
                            self._get_status_message(valid_request),
                            "Use %s as the content type" % self.content_type
                        )
                    )
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "No ID specified"
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _check_and_get_test_group(self, test_group_id):
        """Verify that the test group ID passed is valid, and get it.

        :param test_group_id: The ID of the test group associated with the test
        case
        :type test_group_id: string
        :return A 3-tuple: the test group id, the test group name, an error
        message in case of errors.
        """
        group_oid = None
        group_name = None
        error = None

        try:
            group_oid = bson.objectid.ObjectId(test_group_id)
            test_group = utils.db.find_one2(
                self.db[models.TEST_GROUP_COLLECTION],
                group_oid,
                fields=[models.ID_KEY, models.NAME_KEY])

            if not test_group:
                group_oid = None
                error = "Test group with ID '%s' not found" % test_group_id
            else:
                group_name = test_group[models.NAME_KEY]
        except bson.errors.InvalidId, ex:
            error = "Test group ID '%s' is not valid" % test_group_id
            self.log.exception(ex)
            self.log.error(error)

        return group_oid, group_name, error
