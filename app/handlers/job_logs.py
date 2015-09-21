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

"""The RequestHandler for /job/<id>/logs URLs."""

import bson

import handlers.base as hbase
import handlers.common.query
import handlers.response as hresponse
import models
import models.error_summary as errsummary
import utils.db


# pylint: disable=too-many-public-methods
class JobLogsHandler(hbase.BaseHandler):
    """Retrieve the parsed build logs of a single job ID."""

    def __init__(self, application, request, **kwargs):
        super(JobLogsHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.ERRORS_SUMMARY_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return errsummary.ERROR_SUMMARY_VALID_KEYS.get(method, None)

    def execute_delete(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def execute_put(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def execute_post(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def _get_one(self, doc_id, **kwargs):
        response = hresponse.HandlerResponse()
        result = None

        try:
            obj_id = bson.objectid.ObjectId(doc_id)
            result = utils.db.find_one2(
                self.collection,
                {models.JOB_ID_KEY: obj_id},
                fields=handlers.common.query.get_query_fields(
                    self.get_query_arguments)
            )

            if result:
                # result here is returned as a dictionary from mongodb
                response.result = result
            else:
                response.status_code = 404
                response.reason = "Resource '%s' not found" % doc_id
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Provided doc ID '%s' is not valid", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID value provided"

        return response
