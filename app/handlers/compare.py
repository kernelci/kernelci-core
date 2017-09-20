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

"""The RequestHandler to handle 'compare' requests."""

try:
    import simplejson as json
except ImportError:
    import json

import bson

import handlers.base as hbase
import handlers.common
import handlers.response as hresponse
import models
import models.compare as mcompare
import taskqueue.tasks.compare as taskq
import utils.db
import utils.validator as validator


# pylint: disable=too-many-public-methods
class CompareHandler(hbase.BaseHandler):
    """Handle the 'compare' URL resources."""

    def __init__(self, application, request, **kwargs):
        self.resource = None
        super(CompareHandler, self).__init__(application, request, **kwargs)

    # pylint: disable=arguments-differ
    def initialize(self, resource):
        """Handle the keyword arguments passed via URL definition.

        :param resource: The name of the database resource where to look for
        data.
        :type resource: str
        """
        self.resource = resource

    def _valid_compare_keys(self, method):
        """Get the valid keys associated with this resource.

        :param method: The HTTP method.
        :type method: str
        :return None or a list of valid keys.
        """
        valid_keys = None
        resource_keys = mcompare.COMPARE_VALID_KEYS.get(self.resource, None)
        if resource_keys:
            valid_keys = resource_keys.get(method, None)
        return valid_keys

    @property
    def collection(self):
        return self.db[mcompare.COMPARE_RESOURCE_COLLECTIONS[self.resource]]

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None
        valid_token, token = self.validate_req_token("POST")

        if valid_token:
            valid_request = handlers.common.request.valid_post_request(
                self.request.headers, self.request.remote_ip)

            if valid_request == 200:
                try:
                    json_obj = json.loads(self.request.body.decode("utf8"))

                    valid_json, errors = validator.is_valid_json(
                        json_obj, self._valid_compare_keys("POST"))
                    if valid_json:
                        kwargs["json_obj"] = json_obj
                        kwargs["token"] = token

                        response = self._post(*args, **kwargs)
                        response.errors = errors
                    else:
                        response = hresponse.HandlerResponse(400)
                        response.reason = "Provided JSON is not valid"
                        response.errors = errors
                except ValueError, ex:
                    self.log.exception(ex)
                    error = "No JSON data found in the POST request"
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
            response = hresponse.HandlerResponse(403)

        return response

    def _post(self, *args, **kwargs):
        """Execute the real POST operations."""
        response = hresponse.HandlerResponse()

        task = None
        if self.resource == "job":
            task = taskq.calculate_job_delta
        elif self.resource == "build":
            task = taskq.calculate_build_delta
        else:
            task = taskq.calculate_boot_delta

        res = task.apply_async(
            [kwargs["json_obj"]],
            kwargs={
                "db_options": self.settings["dboptions"],
            }
        )

        # With the while-loop it is faster to get the results back.
        # Like ~40ms with, ~500ms without.
        while not res.ready():
            pass
        status_code, result, doc_id, errors = res.get()

        response.status_code = status_code
        response.result = result
        if doc_id:
            response.headers = {
                "Location": "/%s/compare/%s/" % (self.resource, str(doc_id)),
                "X-Kernelci-Compare-Id": str(doc_id)
            }

        return response

    def execute_put(self, *args, **kwargs):
        """Execute PUT pre-operations."""
        return hresponse.HandlerResponse(501)

    def execute_delete(self, *args, **kwargs):
        """Execute DELETE pre-operations."""
        return hresponse.HandlerResponse(501)

    def execute_get(self, *args, **kwargs):
        """This is the actual GET operation.

        It is done in this way so that subclasses can implement a different
        token authorization if necessary.
        """
        response = None
        valid_token, token = self.validate_req_token("GET")

        if valid_token:
            kwargs["token"] = token
            get_id = kwargs.get("id", None)

            if get_id:
                response = self._get_one(get_id, **kwargs)
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "No ID specified"
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _get_one(self, doc_id, **kwargs):
        """Get just one single document from the collection.

        Subclasses should override this method and implement their own
        search functionalities. This is a general one.
        It should return a `HandlerResponse` object, with the `result`
        attribute set with the operation results.

        :return A `HandlerResponse` object.
        """
        response = hresponse.HandlerResponse()
        result = None

        try:
            obj_id = bson.objectid.ObjectId(doc_id)
            result = utils.db.find_one2(
                self.collection, {models.ID_KEY: obj_id})

            if result:
                # result here is returned as a dictionary from mongodb and we
                # extract a list from the "data" key.
                result = result["data"]
                # Inject the _id field.
                result[0][models.ID_KEY] = obj_id

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
