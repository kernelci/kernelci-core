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

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
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
        return hcommon.valid_token_tests

    def execute_put(self, *args, **kwargs):
        """Execute the PUT pre-operations."""
        response = None

        if self.validate_req_token("PUT"):
            if kwargs and kwargs.get("id", None):
                valid_request = self._valid_post_request()

                if valid_request == 200:
                    try:
                        json_obj = json.loads(self.request.body.decode("utf8"))

                        valid_json, j_reason = validator.is_valid_json(
                            json_obj, self._valid_keys("PUT"))
                        if valid_json:
                            kwargs["json_obj"] = json_obj
                            kwargs["db_options"] = self.settings["dboptions"]
                            kwargs["reason"] = j_reason
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
            response.reason = hcommon.NOT_VALID_TOKEN

        return response
