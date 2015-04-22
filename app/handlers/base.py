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

"""The base RequestHandler that all subclasses should inherit from."""

try:
    import simplejson as json
except ImportError:
    import json

import bson
import httplib
import tornado
import tornado.escape
import tornado.gen
import tornado.web
import types

import handlers.common as hcommon
import handlers.response as hresponse
import models
import utils
import utils.db
import utils.log
import utils.validator as validator


STATUS_MESSAGES = {
    404: "Resource not found",
    405: "Operation not allowed",
    415: "Wrong content type defined",
    420: "No JSON data found",
    500: "Internal database error",
    501: "Method not implemented",
    506: "Wrong response type from database"
}


# pylint: disable=unused-argument
# pylint: disable=too-many-public-methods
# pylint: disable=no-self-use
class BaseHandler(tornado.web.RequestHandler):
    """The base handler."""

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self._db = None

    @property
    def executor(self):
        """The executor where async function should be run."""
        return self.settings["executor"]

    @property
    def collection(self):
        """The name of the database collection for this object."""
        return None

    @property
    def content_type(self):
        """The accepted content-type header."""
        return hcommon.ACCEPTED_CONTENT_TYPE

    # pylint: disable=invalid-name
    @property
    def db(self):
        """The database instance associated with the object."""
        if self._db is None:
            db_options = self.settings["dboptions"]
            client = self.settings["client"]

            db_pwd = db_options["dbpassword"]
            db_user = db_options["dbuser"]

            self._db = client[models.DB_NAME]

            if all([db_user, db_pwd]):
                self._db.authenticate(db_user, password=db_pwd)

        return self._db

    @property
    def log(self):
        """The logger of this object."""
        return utils.log.get_log(debug=self.settings["debug"])

    @staticmethod
    def _valid_keys(method):
        """The accepted keys for the valid sent content type.

        :param method: The HTTP method name that originated the request.
        :type str
        :return A list of keys that the method accepts.
        """
        return []

    @staticmethod
    def _token_validation_func():
        """The function that should be used to validate the token.

        :return A function.
        """
        return hcommon.valid_token_general

    def _get_status_message(self, status_code):
        """Get custom error message based on the status code.

        :param status_code: The status code to get the message of.
        :type int
        :return The error message string.
        """
        message = STATUS_MESSAGES.get(status_code, None)
        if not message:
            # If we do not have a custom message, try to see into
            # the Python lib for the default one or fail safely.
            message = httplib.responses.get(
                status_code, "Unknown status code returned")
        return message

    def write(self, future):
        """Write the response back to the requestor."""
        status_code = 200
        headers = {}
        result = {}

        if isinstance(future, hresponse.HandlerResponse):
            status_code = future.status_code
            reason = future.reason or self._get_status_message(status_code)
            headers = future.headers
            to_dump = future.to_dict()
        elif isinstance(future, types.DictionaryType):
            status_code = future.get("code", 200)
            reason = future.get(
                "reason", self._get_status_message(status_code))
            to_dump = future
        else:
            status_code = 506
            reason = self._get_status_message(status_code)
            to_dump = dict(code=status_code, reason=reason)

        result = json.dumps(
            to_dump,
            default=bson.json_util.default,
            ensure_ascii=False,
            separators=(",", ":")
        )

        self.set_status(status_code=status_code, reason=reason)
        self._write_buffer.append(tornado.escape.utf8(result))
        self.set_header("Content-Type", hcommon.DEFAULT_RESPONSE_TYPE)

        if headers:
            for key, val in headers.iteritems():
                self.add_header(key, val)

        self.finish()

    def write_error(self, status_code, **kwargs):
        if kwargs.get("message", None):
            status_message = kwargs["message"]
        else:
            status_message = self._get_status_message(status_code)

        if status_message:
            self.write(dict(code=status_code, reason=status_message))
        else:
            super(BaseHandler, self).write_error(status_code, kwargs)

    def _has_valid_content_type(self):
        """Check if the request content type is the one expected.

        By default, content must be `application/json`.

        :return True or False.
        """
        valid_content = False

        if "Content-Type" in self.request.headers.keys():
            if self.request.headers["Content-Type"].startswith(
                    self.content_type):
                valid_content = True
            else:
                self.log.error(
                    "Received wrong content type ('%s') from IP '%s'",
                    self.request.headers["Content-Type"],
                    self.request.remote_ip
                )

        return valid_content

    @tornado.gen.coroutine
    def put(self, *args, **kwargs):
        future = yield self.executor.submit(self.execute_put, *args, **kwargs)
        self.write(future)

    def execute_put(self, *args, **kwargs):
        """Execute the PUT pre-operations."""
        response = None
        valid_token, token = self.validate_req_token("PUT")

        if valid_token:
            kwargs["token"] = token
            response = self._put(*args, **kwargs)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _put(self, *args, **kwargs):
        """Placeholder method - used internally.

        This is called by the actual method that implements PUT request.
        Subclasses should provide their own implementation.

        It must return a `HandlerResponse` object with the appropriate status
        code and if necessary its custom message.

        :return A `HandlerResponse` object.
        """
        return hresponse.HandlerResponse(501)

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        future = yield self.executor.submit(self.execute_post, *args, **kwargs)
        self.write(future)

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None
        valid_token, token = self.validate_req_token("POST")

        if valid_token:
            valid_request = self._valid_post_request()

            if valid_request == 200:
                try:
                    json_obj = json.loads(self.request.body.decode("utf8"))

                    valid_json, errors = validator.is_valid_json(
                        json_obj, self._valid_keys("POST"))
                    if valid_json:
                        kwargs["json_obj"] = json_obj
                        kwargs["token"] = token
                        kwargs["db_options"] = self.settings["dboptions"]

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
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _valid_post_request(self):
        """Check that a POST request is valid.

        :return 200 in case is valid, 415 if not.
        """
        return_code = 200

        if not self._has_valid_content_type():
            return_code = 415

        return return_code

    def _post(self, *args, **kwargs):
        """Placeholder method - used internally.

        This is called by the actual method that implements POST request.
        Subclasses should provide their own implementation.

        It must return a `HandlerResponse` object with the appropriate status
        code and if necessary its custom message.

        This method will receive a named argument containing the JSON object
        with the POST request data. The argument is called `json_obj`.
        It will also receive a named argument containing the mongodb database
        connection parameters. The argument is called `db_options`.

        :return A `HandlerResponse` object.
        """
        return hresponse.HandlerResponse(501)

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        future = yield self.executor.submit(
            self.execute_delete, *args, **kwargs)
        self.write(future)

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None
        valid_token, token = self.validate_req_token("DELETE")

        if valid_token:
            kwargs["token"] = token
            del_id = kwargs.get("id", None)

            if del_id:
                response = self._delete(del_id, **kwargs)
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "No ID value specified"
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _delete(self, doc_id, **kwargs):
        """Placeholder method - used internally.

        This is called by the actual method that implements DELETE request.
        Subclasses should provide their own implementation.

        It must return a `HandlerResponse` object with the appropriate status
        code and if necessary its custom message.

        :param doc_id: The ID of the document to delete.
        :return A `HandlerResponse` object.
        """
        return hresponse.HandlerResponse(501)

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        future = yield self.executor.submit(self.execute_get, *args, **kwargs)
        self.write(future)

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
                response = self._get(**kwargs)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

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
            result = utils.db.find_one(
                self.collection,
                [obj_id],
                fields=hcommon.get_query_fields(self.get_query_arguments)
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

    def _get(self, **kwargs):
        """Get all the documents in the collection.

        The returned results can be tweaked with the supported query arguments.

        Subclasses should override this method and implement their own
        search functionalities. This is a general one.
        It should return a `HandlerResponse` object, with the `result`
        attribute set with the operation results.

        :return A `HandlerResponse` object.
        """
        response = hresponse.HandlerResponse()
        spec, sort, fields, skip, limit, unique = self._get_query_args()

        if unique:
            response.result = utils.db.aggregate(
                self.collection,
                unique,
                match=spec,
                sort=sort,
                fields=fields,
                limit=limit
            )
        else:
            result, count = utils.db.find_and_count(
                self.collection,
                limit,
                skip,
                spec=spec,
                fields=fields,
                sort=sort
            )

            if count > 0:
                response.result = result
            else:
                response.result = []

            response.count = count

        response.limit = limit
        return response

    def _get_query_args(self, method="GET"):
        """Retrieve all the arguments from the query string.

        This method will return the `spec`, `sort` and `fields` data structures
        that can be used to perform MongoDB queries, the aggregate value to
        perform aggregation, and the `skip` and `limit` values.

        :return A tuple with, in order: `spec`, `sort`, `fields`, `skip`,
        `limit` and `aggregate` values.
        """
        spec = {}
        sort = None
        fields = None
        skip = 0
        limit = 0
        unique = None

        if self.request.arguments:
            spec, sort, fields, skip, limit, unique = \
                hcommon.get_all_query_values(
                    self.get_query_arguments, self._valid_keys(method))

        return spec, sort, fields, skip, limit, unique

    # TODO: cache the validated token.
    def validate_req_token(self, method):
        """Validate the request token.

        :param method: The HTTP verb we are validating.
        :return A 2-tuple: True or False; the token object.
        """
        valid_token = False
        token = None

        req_token = self.request.headers.get(hcommon.API_TOKEN_HEADER, None)
        remote_ip = self.request.remote_ip
        master_key = self.settings.get(hcommon.MASTER_KEY, None)

        if req_token:
            valid_token, token = self._token_validation(
                req_token, method, remote_ip, master_key)

        if not valid_token:
            self.log.info(
                "Token not authorized for IP address %s - Token: %s",
                self.request.remote_ip, req_token)

        return valid_token, token

    def _token_validation(self, req_token, method, remote_ip, master_key):
        """Perform the real token validation.

        :param req_token: The token as taken from the request.
        :type req_token: string
        :param method: The HTTP verb to validate.
        :type method: string
        :param remote_ip: The IP address originating the request.
        :param master_key: The default master key.
        :return A 2-tuple: True or False; the token object.
        """
        valid_token = False
        token = None
        token_obj = self._find_token(req_token, self.db)

        if token_obj:
            valid_token, token = hcommon.validate_token(
                token_obj,
                method,
                remote_ip,
                self._token_validation_func()
            )

        return valid_token, token

    # TODO: cache the token from the DB.
    @staticmethod
    def _find_token(token, db_conn):
        """Find a token in the database.

        :param token: The token to find.
        :return A json object, or nothing.
        """
        return utils.db.find_one2(
            db_conn[models.TOKEN_COLLECTION], {models.TOKEN_KEY: token})
