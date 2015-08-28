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

"""The RequestHandler to handle 'distinct' requests."""

import handlers.base as hbase
import handlers.common.query
import handlers.response as hresponse
import models


# pylint: disable=too-many-public-methods
class DistinctHandler(hbase.BaseHandler):
    """Handle the 'distinct' URL resources."""

    def __init__(self, application, request, **kwargs):
        self.resource = None
        super(DistinctHandler, self).__init__(application, request, **kwargs)

    # pylint: disable=arguments-differ
    def initialize(self, resource):
        """Handle the keyword arguments passed via URL definition.

        :param resource: The name of the database resource where to look for
        data.
        :type resource: str
        """
        self.resource = resource

    @property
    def collection(self):
        return self.db[self.resource]

    def _valid_distinct_keys(self, method):
        """Get the valid keys associated with this resource.

        :param method: The HTTP method.
        :type method: str
        :return None or a list of valid keys.
        """
        valid_keys = None
        resource_keys = models.DISTINCT_VALID_KEYS.get(self.resource, None)
        if resource_keys:
            valid_keys = resource_keys.get(method, None)
        return valid_keys

    def execute_post(self, *args, **kwargs):
        """Execute POST pre-operations."""
        return hresponse.HandlerResponse(501)

    def execute_put(self, *args, **kwargs):
        """Execute PUT pre-operations."""
        return hresponse.HandlerResponse(501)

    def execute_delete(self, *args, **kwargs):
        """Execute DELETE pre-operations."""
        return hresponse.HandlerResponse(501)

    def execute_get(self, *args, **kwargs):
        """Handle GET pre-operations."""
        response = None
        valid_token, token = self.validate_req_token("GET")

        if valid_token:
            kwargs["token"] = token
            field = kwargs.get("field", None)

            if all([field, self._valid_distinct_field(field)]):
                if self.request.arguments:
                    response = self._get_distinct_query(field)
                else:
                    response = self._get_distinct_field(field)
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "No field specified or field not valid"
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _valid_distinct_field(self, field):
        """Make sure the requested distinct field is valid.

        :param field: The field name to validate.
        :type field: str
        :return True or False.
        """
        valid_field = False
        if field:
            valid_field = \
                field in models.DISTINCT_VALID_FIELDS.get(self.resource, [])

        return valid_field

    def _get_distinct_query(self, field):
        """Get the distinct values for the specified field and query.

        The query parameters are parsed and a search is performed before
        retrieving the unique values.

        :param field: The field to get the distinct values of.
        :type field: str
        :return A HandlerResponse instance.
        """
        response = hresponse.HandlerResponse(200)

        fields = None
        limit = 0
        skip = 0
        sort = None
        spec = {}

        spec, sort, fields, skip, limit, _ = \
            handlers.common.query.get_all_query_values(
                self.get_query_arguments, self._valid_distinct_keys("GET"))

        db_result = self.collection.find(
            spec=spec, limit=limit, skip=skip, fields=fields, sort=sort)

        response.result = db_result.distinct(field)
        response.count = len(response.result)

        return response

    def _get_distinct_field(self, field):
        """Get the distinct values for the specified field.

        :param field: The field to get the distinct values of.
        :type field: str
        :return A HandlerResponse instance.
        """
        response = hresponse.HandlerResponse()
        response.result = self.collection.distinct(field)
        response.count = len(response.result)

        return response
