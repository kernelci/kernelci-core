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

"""The RequestHandler for /report URLs."""

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models


class ReportHandler(hbase.BaseHandler):
    """Handle the /report[s] URLs."""

    def __init__(self, application, request, **kwargs):
        super(ReportHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.REPORT_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return hcommon.REPORT_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return hcommon.valid_token_th

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None

        if self.validate_req_token("DELETE"):
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None

        if self.validate_req_token("POST"):
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response
