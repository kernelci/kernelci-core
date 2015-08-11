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

"""The request handler for the /statistics URL."""

import handlers.base as hbase
import handlers.response as hresponse
import models


class StatisticsHandler(hbase.BaseHandler):
    """Handle request to the statistics API resource."""

    def __init__(self, application, request, **kwargs):
        super(StatisticsHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.DAILY_STATS_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.STATISTICS_VALID_KEYS.get(method, None)

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None
        valid_token, _ = self.validate_req_token("DELETE")

        if valid_token:
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None
        valid_token, _ = self.validate_req_token("POST")

        if valid_token:
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def execute_put(self, *args, **kwargs):
        """Execute the PUT pre-operations.

        Checks that everything is OK to perform a PUT.
        """
        response = None
        valid_token, _ = self.validate_req_token("PUT")

        if valid_token:
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)

        return response
