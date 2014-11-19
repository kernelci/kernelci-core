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

"""The request handler for bisect URLs."""

import bson
import functools
import tornado
import tornado.web

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import taskqueue.tasks as taskt
import utils.db


class BisectHandler(hbase.BaseHandler):
    """Handler used to trigger bisect operations on the data."""

    def __init__(self, application, request, **kwargs):
        super(BisectHandler, self).__init__(application, request, **kwargs)

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        self.executor.submit(
            functools.partial(self.execute_get, *args, **kwargs)
        ).add_done_callback(
            lambda future:
            tornado.ioloop.IOLoop.instance().add_callback(
                functools.partial(self._create_valid_response, future.result())
            )
        )

    @property
    def collection(self):
        return models.BISECT_COLLECTION

    def execute_get(self, *args, **kwargs):
        """This is the actual GET operation.

        It is done in this way so that subclasses can implement a different
        token authorization if necessary.
        """
        response = None

        if self.validate_req_token("GET"):
            if kwargs:
                collection = kwargs.get("collection", None)
                doc_id = kwargs.get("id", None)
                if all([collection, doc_id]):
                    fields = None
                    if self.request.arguments:
                        fields = hcommon.get_query_fields(
                            self.get_query_arguments
                        )
                    try:
                        obj_id = bson.objectid.ObjectId(doc_id)
                        bisect_result = utils.db.find_one(
                            self.db[self.collection],
                            [obj_id],
                            field=models.NAME_KEY,
                            fields=fields
                        )
                        if bisect_result:
                            response = hresponse.HandlerResponse(200)
                            response.result = bisect_result
                        else:
                            response = self._get_bisect(
                                collection, doc_id, fields
                            )
                    except bson.errors.InvalidId, ex:
                        self.log.exception(ex)
                        self.log.error(
                            "Wrong ID '%s' value passed as object ID", doc_id)
                        response = hresponse.HandlerResponse(400)
                        response.reason = "Wrong ID value passed as object ID"
                else:
                    response = hresponse.HandlerResponse(400)
            else:
                response = hresponse.HandlerResponse(400)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _get_bisect(self, collection, doc_id, fields=None):
        """Retrieve the bisect data.

        :param collection: The name of the collection to operate on.
        :type collection: str
        :param doc_id: The ID of the document to execute the bisect on.
        :type doc_id: str
        :param fields: A `fields` data structure with the fields to return or
        exclude. Default to None.
        :type fields: list or dict
        :return A `HandlerResponse` object.
        """
        response = None

        if collection in models.BISECT_VALID_COLLECTIONS:
            db_options = self.settings["dboptions"]

            if collection == models.BOOT_COLLECTION:
                response = self.execute_boot_bisect(doc_id, db_options, fields)
        else:
            response = hresponse.HandlerResponse(400)
            response.reason = (
                "Provided bisect collection '%s' is not valid" % collection
            )

        return response

    @staticmethod
    def execute_boot_bisect(doc_id, db_options, fields=None):
        """Execute the boot bisect operation.

        :param doc_id: The ID of the document to execute the bisect on.
        :type doc_id: str
        :param db_options: The mongodb database connection parameters.
        :type db_options: dict
        :param fields: A `fields` data structure with the fields to return or
        exclude. Default to None.
        :type fields: list or dict
        :return A `HandlerResponse` object.
        """
        response = hresponse.HandlerResponse()

        result = taskt.boot_bisect.apply_async([doc_id, db_options, fields])
        while not result.ready():
            pass

        response.status_code, response.result = result.get()
        if response.status_code == 404:
            response.reason = "Boot report not found"
        elif response.status_code == 400:
            response.reason = "Boot report cannot be bisected: is it failed?"
        return response
