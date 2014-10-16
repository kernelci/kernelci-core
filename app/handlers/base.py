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
    get_aggregate_value,
    get_query_fields,
    get_query_sort,
    get_query_spec,
    get_and_add_date_range,
    get_skip_and_limit,
)
from handlers.decorators import protected
from handlers.response import HandlerResponse
from models import (
    DB_NAME,
)
from utils.db import (
    aggregate,
    find_and_count,
    find_one,
)
from utils.log import get_log
from utils.validator import is_valid_json


class BaseHandler(RequestHandler):
    """The base handler."""

    ACCEPTED_CONTENT_TYPE = 'application/json'
    DEFAULT_RESPONSE_TYPE = 'application/json; charset=UTF-8'

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

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
        return self.settings['client'][DB_NAME]

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

    def _get_status_message(self, status_code):
        """Get custom error message based on the status code.

        :param status_code: The status code to get the message of.
        :type int
        :return The error message string.
        """
        status_messages = {
            404: 'Resource not found',
            405: 'Operation not allowed',
            415: (
                'Please use "%s" as the default media type' %
                self.accepted_content_type
            ),
            420: 'No JSON data found',
            500: 'Internal database error',
            501: 'Method not implemented',
            506: 'Wrong response type from database'
        }

        message = status_messages.get(status_code, None)
        if not message:
            # If we do not have a custom message, try to see into
            # the Python lib for the default one or fail safely.
            message = httplib.responses.get(
                status_code, "Unknown status code returned")
        return message

    @property
    def accepted_content_type(self):
        """The accepted Content-Type for PUT requests.

        Defaults to 'application/json'.
        """
        return self.ACCEPTED_CONTENT_TYPE

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
        self.set_header('Content-Type', self.DEFAULT_RESPONSE_TYPE)

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
                    self.accepted_content_type:
                valid_content = True
            else:
                self.log.error(
                    "Received wrong content type ('%s') from IP '%s'",
                    self.request.headers['Content-Type'],
                    self.request.remote_ip
                )

        return valid_content

    @protected("POST")
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
        valid_request = self._valid_post_request()

        if valid_request == 200:
            try:
                json_obj = json.loads(self.request.body.decode('utf8'))

                if is_valid_json(json_obj, self._valid_keys('POST')):
                    kwargs['json_obj'] = json_obj
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

        :return A `HandlerResponse` object.
        """
        return HandlerResponse(501)

    @protected("DELETE")
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

        if kwargs and kwargs.get('id', None):
            response = self._delete(kwargs['id'])
        else:
            response = HandlerResponse(400)
            response.reason = self._get_status_message(400)
            response.result = None

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

    @protected("GET")
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
        if kwargs and kwargs.get('id', None):
            response = self._get_one(kwargs['id'])
        else:
            response = self._get(**kwargs)

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
            self.log.info("Performing aggregation on %s", unique)
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
            query_args_func = self.get_query_arguments

            spec = get_query_spec(
                query_args_func,
                valid_keys=self._valid_keys(method)
            )
            spec = get_and_add_date_range(spec, query_args_func)
            sort = get_query_sort(query_args_func)
            fields = get_query_fields(query_args_func)
            skip, limit = get_skip_and_limit(query_args_func)
            unique = get_aggregate_value(query_args_func)

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
