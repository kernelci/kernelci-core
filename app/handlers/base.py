# Copyright (C) 2014 Linaro Ltd.
#
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

import httplib
import json
import tornado

from bson.json_util import default
from functools import partial
from tornado.web import (
    RequestHandler,
    asynchronous,
)

from handlers.common import (
    ACCEPTED_CONTENT_TYPE,
    API_TOKEN_HEADER,
    DEFAULT_RESPONSE_TYPE,
    MASTER_KEY,
    NOT_VALID_TOKEN,
    get_all_query_values,
    get_query_fields,
    valid_token_general,
    validate_token,
)
from handlers.response import HandlerResponse
from models import (
    DB_NAME,
    TOKEN_COLLECTION,
    TOKEN_KEY,
)
from utils.db import (
    aggregate,
    find_and_count,
    find_one,
)
from utils.log import get_log
from utils.validator import is_valid_json


STATUS_MESSAGES = {
    404: 'Resource not found',
    405: 'Operation not allowed',
    415: (
        'Please use "%s" as the default media type' %
        ACCEPTED_CONTENT_TYPE
    ),
    420: 'No JSON data found',
    500: 'Internal database error',
    501: 'Method not implemented',
    506: 'Wrong response type from database'
}


class BaseHandler(RequestHandler):
    """The base handler."""

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self._db = None

    @property
    def executor(self):
        """The executor where async function should be run."""
        return self.settings['executor']

    @property
    def collection(self):
        """The name of the database collection for this object."""
        return None

    @property
    def db(self):
        """The database instance associated with the object."""
        if self._db is None:
            db_options = self.settings['dboptions']
            client = self.settings['client']

            db_pwd = db_options['dbpassword']
            db_user = db_options['dbuser']

            self._db = client[DB_NAME]

            if all([db_user, db_pwd]):
                self._db.authenticate(db_user, password=db_pwd)

        return self._db

    @property
    def log(self):
        """The logger of this object."""
        return get_log(debug=self.settings['debug'])

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
        return valid_token_general

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

    def _create_valid_response(self, response):
        """Create a valid JSON response based on its type.

        :param response: The response we have from a query to the database.
        :type HandlerResponse
        """
        status_code = 200
        headers = {}
        result = {}

        if isinstance(response, HandlerResponse):
            status_code = response.status_code
            reason = response.reason or self._get_status_message(status_code)
            headers = response.headers
            result = json.dumps(response.to_dict(), default=default)
        else:
            status_code = 506
            reason = self._get_status_message(status_code)
            result = dict(code=status_code, reason=reason)

        self.set_status(status_code=status_code, reason=reason)
        self.write(result)
        self.set_header('Content-Type', DEFAULT_RESPONSE_TYPE)

        if headers:
            for key, val in headers.iteritems():
                self.add_header(key, val)

        self.finish()

    def _has_valid_content_type(self):
        """Check if the request content type is the one expected.

        By default, content must be `application/json`.

        :return True or False.
        """
        valid_content = False

        if 'Content-Type' in self.request.headers.keys():
            if self.request.headers['Content-Type'] == \
                    ACCEPTED_CONTENT_TYPE:
                valid_content = True
            else:
                self.log.error(
                    "Received wrong content type ('%s') from IP '%s'",
                    self.request.headers['Content-Type'],
                    self.request.remote_ip
                )

        return valid_content

    @asynchronous
    def post(self, *args, **kwargs):
        self.executor.submit(
            partial(self.execute_post, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result())
            )
        )

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None

        if self.validate_req_token("POST"):
            valid_request = self._valid_post_request()

            if valid_request == 200:
                try:
                    json_obj = json.loads(self.request.body.decode('utf8'))

                    if is_valid_json(json_obj, self._valid_keys('POST')):
                        kwargs['json_obj'] = json_obj
                        kwargs['db_options'] = self.settings['dboptions']
                        response = self._post(*args, **kwargs)
                    else:
                        response = HandlerResponse(400)
                        response.reason = "Provided JSON is not valid"
                        response.result = None
                except ValueError:
                    error = "No JSON data found in the POST request"
                    self.log.error(error)
                    response = HandlerResponse(422)
                    response.reason = error
                    response.result = None
            else:
                response = HandlerResponse(valid_request)
                response.reason = self._get_status_message(valid_request)
                response.result = None
        else:
            response = HandlerResponse(403)
            response.reason = NOT_VALID_TOKEN

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
        return HandlerResponse(501)

    @asynchronous
    def delete(self, *args, **kwargs):
        self.executor.submit(
            partial(self.execute_delete, *args, **kwargs)
        ).add_done_callback(
            lambda future:
            tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result())
            )
        )

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None

        if self.validate_req_token("DELETE"):
            if kwargs and kwargs.get('id', None):
                response = self._delete(kwargs['id'])
            else:
                response = HandlerResponse(400)
                response.reason = self._get_status_message(400)
                response.result = None
        else:
            response = HandlerResponse(403)
            response.status = NOT_VALID_TOKEN

        return response

    def _delete(self, doc_id):
        """Placeholder method - used internally.

        This is called by the actual method that implements DELETE request.
        Subclasses should provide their own implementation.

        It must return a `HandlerResponse` object with the appropriate status
        code and if necessary its custom message.

        :param doc_id: The ID of the documento to delete.
        :return A `HandlerResponse` object.
        """
        return HandlerResponse(501)

    @asynchronous
    def get(self, *args, **kwargs):
        self.executor.submit(
            partial(self.execute_get, *args, **kwargs)
        ).add_done_callback(
            lambda future:
            tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result())
            )
        )

    def execute_get(self, *args, **kwargs):
        """This is the actual GET operation.

        It is done in this way so that subclasses can implement a different
        token authorization if necessary.
        """
        response = None

        if self.validate_req_token("GET"):
            if kwargs and kwargs.get("id", None):
                response = self._get_one(kwargs["id"])
            else:
                response = self._get(**kwargs)
        else:
            response = HandlerResponse(403)
            response.reason = NOT_VALID_TOKEN

        return response

    def _get_one(self, doc_id):
        """Get just one single document from the collection.

        Sublcasses should override this method and implement their own
        search functionalities. This is a general one.
        It should return a `HandlerResponse` object, with the `result`
        attribute set with the operation results.

        :return A `HandlerResponse` object.
        """
        response = HandlerResponse()
        result = find_one(
            self.collection,
            doc_id,
            fields=get_query_fields(self.get_query_arguments)
        )

        if result:
            # result here is returned as a dictionary from mongodb
            response.result = result
        else:
            response.status_code = 404
            response.reason = "Resource '%s' not found" % doc_id
            response.result = None

        return response

    def _get(self, **kwargs):
        """Get all the documents in the collection.

        The returned results can be tweaked with the supported query arguments.

        Sublcasses should override this method and implement their own
        search functionalities. This is a general one.
        It should return a `HandlerResponse` object, with the `result`
        attribute set with the operation results.

        :return A `HandlerResponse` object.
        """
        response = HandlerResponse()
        spec, sort, fields, skip, limit, unique = self._get_query_args()

        if unique:
            response.result = aggregate(
                self.collection,
                unique,
                sort=sort,
                fields=fields,
                match=spec,
                limit=limit
            )
        else:
            result, count = find_and_count(
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
            spec, sort, fields, skip, limit, unique = get_all_query_values(
                self.get_query_arguments, self._valid_keys(method)
            )

        return (spec, sort, fields, skip, limit, unique)

    def write_error(self, status_code, **kwargs):
        if kwargs.get('message', None):
            status_message = kwargs['message']
        else:
            status_message = self._get_status_message(status_code)

        if status_message:
            self.set_status(status_code, status_message)
            self.write(dict(code=status_code, message=status_message))
            self.finish()
        else:
            super(BaseHandler, self).write_error(status_code, kwargs)

    # TODO: cache the validated token.
    def validate_req_token(self, method):
        """Validate the request token.

        :param method: The HTTP verb we are validating.
        :return True or False.
        """
        valid_token = False

        req_token = self.request.headers.get(API_TOKEN_HEADER, None)
        remote_ip = self.request.remote_ip
        master_key = self.settings.get(MASTER_KEY, None)

        if req_token:
            valid_token = self._token_validation(
                req_token, method, remote_ip, master_key
            )

        if not valid_token:
            self.log.info(
                "Token not authorized for IP address %s - Token: %s",
                self.request.remote_ip, req_token
            )

        return valid_token

    def _token_validation(self, req_token, method, remote_ip, master_key):
        valid_token = False
        token_obj = self._find_token(req_token, self.db)

        if token_obj:
            valid_token = validate_token(
                token_obj,
                method,
                remote_ip,
                self._token_validation_func()
            )
        return valid_token

    # TODO: cache the token from the DB.
    @staticmethod
    def _find_token(token, db_conn):
        """Find a token in the database.

        :param token: The token to find.
        :return A json object, or nothing.
        """
        return find_one(db_conn[TOKEN_COLLECTION], [token], field=TOKEN_KEY)
