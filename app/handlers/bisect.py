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
import tornado.gen

import handlers.base as hbase
import handlers.common.query
import handlers.response as hresponse
import models
import taskqueue.tasks
import taskqueue.tasks.bisect as taskt
import utils.db


# pylint: disable=too-many-public-methods
class BisectHandler(hbase.BaseHandler):
    """Handler used to trigger bisect operations on the data."""

    def __init__(self, application, request, **kwargs):
        super(BisectHandler, self).__init__(application, request, **kwargs)

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        future = yield self.executor.submit(self.execute_get, *args, **kwargs)
        self.write(future)

    @property
    def collection(self):
        return models.BISECT_COLLECTION

    @staticmethod
    def _valid_keys(method):
        """The accepted keys for the valid sent content type.

        :param method: The HTTP method name that originated the request.
        :type str
        :return A list of keys that the method accepts.
        """
        return models.BISECT_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        """Handle HTTP POST requests

        Update bisection data with received results.
        """
        response = hresponse.HandlerResponse(202)
        response.reason = "Request accepted and being imported"
        json_obj = kwargs["json_obj"]
        bisect_type = json_obj["type"]

        if bisect_type == "boot":
            taskt.import_boot_bisect.apply_async(
                [json_obj],
                link_error=taskqueue.tasks.error_handler.s()
            )
        else:
            response = hresponse.HandlerResponse(400)
            response.reason = "Unknown bisection type: {}".format(bisect_type)

        return response

    def execute_get(self, *args, **kwargs):
        """This is the actual GET operation.

        It is done in this way so that subclasses can implement a different
        token authorization if necessary.
        """
        response = None
        valid_token, _ = self.validate_req_token("GET")

        if valid_token:
            doc_id = kwargs.get("id", None)
            fields = handlers.common.query.get_query_fields(
                self.get_query_arguments)

            if doc_id:
                try:
                    obj_id = bson.objectid.ObjectId(doc_id)
                    bisect_result = utils.db.find_one2(
                        self.db[self.collection], obj_id, fields=fields)

                    if bisect_result:
                        response = hresponse.HandlerResponse()
                        response.result = bisect_result
                    else:
                        response = hresponse.HandlerResponse(404)
                        response.reason = "Resource not found"
                except bson.errors.InvalidId, ex:
                    self.log.exception(ex)
                    self.log.error(
                        "Wrong ID '%s' value passed as object ID", doc_id)
                    response = hresponse.HandlerResponse(400)
                    response.reason = "Wrong ID value passed as object ID"
            else:
                # No ID specified, use the query args.
                spec = handlers.common.query.get_query_spec(
                    self.get_query_arguments, self._valid_keys("GET"))
                collection = spec.pop(models.COLLECTION_KEY, None)

                if collection:
                    response = self._get_bisect(collection, spec, fields)
                else:
                    response = hresponse.HandlerResponse(400)
                    response.reason = (
                        "Missing 'collection' key, cannot process the request")
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _get_bisect(self, collection, spec, fields=None):
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
            if collection == models.BOOT_COLLECTION:
                bisect_func = execute_boot_bisect
                if spec.get(models.COMPARE_TO_KEY, None):
                    bisect_func = execute_boot_bisect_compared_to
                else:
                    # Force the compare_to field to None (null in mongodb)
                    # so that we can search correctly otherwise we can get
                    # multiple results out. This is due to how we store the
                    # bisect calculations in the db.
                    spec[models.COMPARE_TO_KEY] = None

                response = self._bisect(
                    models.BOOT_ID_KEY,
                    spec,
                    bisect_func,
                    fields=fields)
            elif collection == models.BUILD_COLLECTION:
                bisect_func = execute_build_bisect
                if spec.get(models.COMPARE_TO_KEY, None):
                    bisect_func = execute_build_bisect_compared_to
                else:
                    # Force the compare_to field to None (null in mongodb)
                    # so that we can search correctly otherwise we can get
                    # multiple results out. This is due to how we store the
                    # bisect calculations in the db.
                    spec[models.COMPARE_TO_KEY] = None

                response = self._bisect(
                    models.BUILD_ID_KEY,
                    spec,
                    bisect_func,
                    fields=fields)
        else:
            response = hresponse.HandlerResponse(400)
            response.reason = (
                "Provided bisect collection '%s' is not valid" % collection)

        return response

    def _bisect(self, id_key, spec, bisect_func, fields=None):
        """Perform the bisect operation.

        :param id_key: The name of the key that contains the ID value of the
        document we want to bisect.
        :type id_key: string
        :param spec: The spec data structure as retrieved with the request
        query args.
        :type spec: dictionary
        :param bisect_func: The bisect function that should be called. It
        should accept the `doc_id` as string, the database options as
        dictionary and `**kwargs`.
        :type bisect_func: function
        :param fields: A `fields` data structure with the fields to return or
        exclude. Default to None.
        :type fields: list or dict
        :return A HandlerResponse instance.
        """
        response = None
        s_get = spec.get
        doc_id = s_get(id_key, None)

        if doc_id:
            try:
                obj_id = bson.objectid.ObjectId(doc_id)
                spec[id_key] = obj_id

                bisect_result = utils.db.find_one2(
                    self.db[self.collection],
                    spec,
                    fields=fields
                )

                if bisect_result:
                    response = hresponse.HandlerResponse()
                    response.result = bisect_result
                else:
                    kwargs = {
                        "fields": fields,
                        "compare_to": s_get(models.COMPARE_TO_KEY, None)}
                    response = bisect_func(
                        doc_id, self.settings["dboptions"], **kwargs)
            except bson.errors.InvalidId, ex:
                self.log.exception(ex)
                self.log.error(
                    "Wrong ID '%s' value passed as object ID", doc_id)
                response = hresponse.HandlerResponse(400)
                response.reason = "Wrong ID value passed as object ID"
        else:
            response = hresponse.HandlerResponse(400)
            response.reason = "Missing boot ID value to look for"

        return response


def execute_boot_bisect(doc_id, db_options, **kwargs):
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

    result = taskt.boot_bisect.apply_async(
        [doc_id, db_options, kwargs.get("fields", None)])
    while not result.ready():
        pass

    response.status_code, response.result = result.get()
    if response.status_code == 404:
        response.reason = "Boot report not found"
    elif response.status_code == 400:
        response.reason = "Boot report cannot be bisected: is it failed?"
    return response


def execute_boot_bisect_compared_to(doc_id, db_options, **kwargs):
    """Execute the boot bisection compared to another tree.

    :param doc_id: The ID of the document to execute the bisect on.
    :type doc_id: string
    :param db_options: The mongodb database connection parameters.
    :type db_options: dictionary
    :param compare_to: The name of the tree to compare against.
    :type compare_to: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return A `HandlerResponse` object.
    """
    response = hresponse.HandlerResponse()
    compare_to = kwargs.get("compare_to", None)
    fields = kwargs.get("fields", None)

    result = taskt.boot_bisect_compared_to.apply_async(
        [doc_id, compare_to, db_options, fields])
    while not result.ready():
        pass

    response.status_code, response.result = result.get()
    if response.status_code == 404:
        response.reason = (
            "Boot bisection compared to '%s' not found" % compare_to)
    elif response.status_code == 400:
        response.reason = "Boot report cannot be bisected: is it failed?"

    return response


def execute_build_bisect(doc_id, db_options, **kwargs):
    """Execute the build bisect operation.

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

    result = taskt.defconfig_bisect.apply_async(
        [doc_id, db_options, kwargs.get("fields", None)])
    while not result.ready():
        pass

    response.status_code, response.result = result.get()
    if response.status_code == 404:
        response.reason = "Defconfig not found"
    elif response.status_code == 400:
        response.reason = "Defconfig cannot be bisected: is it failed?"

    return response


def execute_build_bisect_compared_to(doc_id, db_options, **kwargs):
    response = hresponse.HandlerResponse()
    compare_to = kwargs.get("compare_to", None)
    fields = kwargs.get("fields", None)

    result = taskt.defconfig_bisect_compared_to.apply_async(
        [doc_id, compare_to, db_options, fields])
    while not result.ready():
        pass

    response.status_code, response.result = result.get()
    if response.status_code == 404:
        response.reason = (
            "Defconfig bisection compared to '%s' not found" % compare_to)
    elif response.status_code == 400:
        response.reason = "Defconfig cannot be bisected: is it failed?"

    return response
