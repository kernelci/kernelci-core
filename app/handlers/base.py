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

import types

from bson.json_util import dumps
from tornado import gen
from tornado.web import (
    RequestHandler,
    asynchronous,
)

from pymongo.cursor import Cursor

from models import DB_NAME
from utils.validator import is_valid_json_put
from utils.db import (
    find_async,
    find_one_async,
)

# Default and maximum limit for how many results to get back from the db.
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class BaseHandler(RequestHandler):
    """The base handler."""

    ACCEPTED_CONTENT_TYPE = 'application/json'

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        """The name of the database collection for this object."""
        return None

    @property
    def db(self):
        """The database instance associated with the object."""
        return self.settings['client'][DB_NAME]

    @property
    def accepted_keys(self):
        """The list of accepted keys to validate a JSON object."""
        return ()

    def _get_status_message(self, status_code):
        """Get custom error message based on the status code.

        :param status_code: The status code to get the message of.
        :type int
        :return The error message string, or None if the code does not have
                a custom message.
        """
        status_messages = {
            200: 'OK',
            400: 'Provided JSON is not valid.',
            404: 'Resource not found.',
            405: 'Operation not allowed.',
            415: (
                'Please use "%s" as the default media type.' %
                self.accepted_content_type
            ),
            500: 'Internal database error.'
        }

        return status_messages.get(status_code, None)

    @property
    def accepted_content_type(self):
        """The accepted Content-Type for PUT requests.

        Defaults to 'application/json'.
        """
        return self.ACCEPTED_CONTENT_TYPE

    def is_valid_put(self, json_obj):
        """Validate PUT requests content.

        :param json_obj: The JSON object to validate.
        :return True or False.
        """
        return is_valid_json_put(json_obj, self.accepted_keys)

    def _create_valid_response(self, response):
        """Create a valid JSON response based on its type.

        :param response: The response we have from a query to the database.
        :return A (int, str) tuple composed of the status code, and the
                message.
        """
        valid_response = (200, self._get_status_message(200))

        if isinstance(response, types.DictionaryType):
            valid_response = (200, dumps(response))
        elif isinstance(response, types.IntType):
            valid_response = (response, self._get_status_message(response))
        elif isinstance(response, Cursor):
            valid_response = (200, dumps(response))
        elif isinstance(response, types.NoneType):
            valid_response = (404, self._get_status_message(404))

        return valid_response

    @asynchronous
    @gen.engine
    def get(self, *args, **kwargs):
        if kwargs and kwargs['id']:
            result = yield gen.Task(
                find_one_async,
                self.collection,
                kwargs['id'],
            )

            status_code, response = self._create_valid_response(result)
            response = dict(code=status_code, message=response)
        else:
            skip = int(self.get_query_argument('skip', default=0))
            limit = int(
                self.get_query_argument('limit', default=DEFAULT_LIMIT)
            )
            if limit > MAX_LIMIT:
                limit = MAX_LIMIT

            result = yield gen.Task(
                find_async,
                self.collection,
                limit,
                skip,
            )

            status_code, response = self._create_valid_response(result)
            response = dict(code=status_code, limit=limit, message=response)

        self.set_status(status_code)
        self.write(response)
        self.finish()

    def write_error(self, status_code, **kwargs):
        status_message = self._get_status_message(status_code)

        if status_message:
            self.set_status(status_code)
            self.write(dict(code=status_code, message=status_message))
            self.finish()
        else:
            super(BaseHandler, self).write_error(status_code)
