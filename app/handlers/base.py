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
import types

from bson.json_util import dumps
from functools import partial
from tornado.web import (
    RequestHandler,
    asynchronous,
)

from models import DB_NAME
from utils.db import (
    find_and_count,
    find_one,
)
from utils.log import get_log
from utils.validator import is_valid_json

# Default limit for how many results to get back: 0 means all.
DEFAULT_LIMIT = 0


class BaseHandler(RequestHandler):
    """The base handler."""

    ACCEPTED_CONTENT_TYPE = 'application/json'

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

    @property
    def executor(self):
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
        return get_log()

    def _valid_keys(self, method):
        """The accepted keys for the valid sent content type.

        :param method: The HTTP method name that originated the request.
        :type str
        :return A list of keys that the method accepts.
        """
        return None

    def _get_status_message(self, status_code):
        """Get custom error message based on the status code.

        :param status_code: The status code to get the message of.
        :type int
        :return The error message string, or None if the code does not have
                a custom message.
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
            501: 'Method not implemented'
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
        :return A (int, str) tuple composed of the status code, and the
                message.
        """
        if isinstance(response, (types.DictionaryType, types.ListType)):
            status, message = 200, dumps(response)
        elif isinstance(response, types.IntType):
            status, message = response, self._get_status_message(response)
        elif isinstance(response, types.NoneType):
            status, message = 404, self._get_status_message(404)
        else:
            status, message = 200, self._get_status_message(200)

        self.set_status(status_code=status, reason=message)
        self.write(dict(code=status, message=message))
        self.finish()

    def _get_callback(self, result):
        """Callback used for GET operations.

        :param limit: The number of elements returned.
        :param result: The result from the future instance. A dictionary with
            at least the `result` key.
        """
        result['result'] = dumps(result['result'])
        result['code'] = 200

        self.set_status(200)
        self.write(result)
        self.finish()

    def _has_xsrf_header(self):
        """Check if the request has the `X-Xsrf-Header` set.

        :return True or False.
        """
        # TODO need token mechanism to authorize requests.
        has_header = False

        if self.request.headers.get('X-Xsrf-Header', None):
            has_header = True

        return has_header

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

        return valid_content

    @asynchronous
    def post(self, *args, **kwargs):

        valid_request = self._valid_post_request()

        if valid_request == 200:
            try:
                json_obj = json.loads(self.request.body.decode('utf8'))

                if is_valid_json(json_obj, self._valid_keys('POST')):
                    self._post(json_obj)
                else:
                    self.send_error(status_code=400)
            except ValueError:
                self.log.error("No JSON data found in the POST request")
                self.write_error(status_code=420)
        else:
            self.write_error(status_code=valid_request)

    def _valid_post_request(self):
        """Check that a POST request is valid.

        :return 200 in case is valid, any other status code if not.
        """
        return_code = 200

        if self._has_xsrf_header():
            if not self._has_valid_content_type():
                return_code = 415
        else:
            return_code = 403

        return return_code

    def _post(self, json_obj):
        """Placeholder method - used internally.

        This is called by the actual method that implements POST request.
        Subclasses should provide their own implementation.

        This will return a status code of 501.

        :param json_obj: A JSON object.
        """
        self.write_error(status_code=501)

    @asynchronous
    def delete(self, *args, **kwargs):
        request_code = self._valid_del_request()

        if request_code == 200:
            if kwargs and kwargs.get('id', None):
                self._delete(kwargs['id'])
            else:
                self.write_error(status_code=400)
        else:
            self.write_error(status_code=request_code)

    def _valid_del_request(self):
        """Check if the DELETE request is valid."""
        return_code = 200

        if not self._has_xsrf_header():
            return_code = 403

        return return_code

    def _delete(self, doc_id):
        """Placeholder method - used internally.

        This is called by the actual method that implements DELETE request.
        Subclasses should provide their own implementation.

        This will return a status code of 501.

        :param doc_id: The ID of the documento to delete.
        """
        self.write_error(status_code=501)

    @asynchronous
    def get(self, *args, **kwargs):
        if kwargs and kwargs.get('id', None):
            self.executor.submit(
                partial(find_one, self.collection, kwargs['id'])
            ).add_done_callback(
                lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._create_valid_response, future.result())
                )
            )
        else:
            skip = int(self.get_query_argument('skip', default=0))
            limit = int(
                self.get_query_argument('limit', default=DEFAULT_LIMIT)
            )

            self.executor.submit(
                partial(self._get, limit, skip)
            ).add_done_callback(
                lambda future:
                tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._get_callback, future.result()))
            )

    def _get(self, limit, skip):
        """Method called by the real GET one.

        For special uses, sublcasses should override this one and provide their
        own implementation.

        By default it executes a search on all the documents in a collection,
        returnig at max `limit` documents.

        It shoul return a dictionary with at least the following fields:
        `result` - that will hold the actual operation result
        `count` - the total number of results available
        `limit` - how many results have been collected
        """
        return find_and_count(self.collection, limit, skip)

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
