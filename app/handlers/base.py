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
from bson import tz_util
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from functools import partial
from pymongo import (
    ASCENDING,
    DESCENDING,
)
from tornado.web import (
    RequestHandler,
    asynchronous,
)

from handlers.decorators import protected
from models import (
    AGGREGATE_KEY,
    CREATED_KEY,
    DATE_RANGE_KEY,
    DB_NAME,
    FIELD_KEY,
    LIMIT_KEY,
    NOT_FIELD_KEY,
    SKIP_KEY,
    SORT_KEY,
    SORT_ORDER_KEY,
)
from utils.db import (
    aggregate,
    find_and_count,
    find_one,
)
from utils.log import get_log
from utils.validator import is_valid_json

# Default value to calculate a date range in case the provided value is
# out of range.
DEFAULT_DATE_RANGE = 15


class BaseHandler(RequestHandler):
    """The base handler."""

    ACCEPTED_CONTENT_TYPE = 'application/json'

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
        return get_log()

    def _valid_keys(self, method):
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

        self.set_status(status_code=status)
        self.write(dict(code=status, result=message))
        self.finish()

    def _get_callback(self, result):
        """Callback used for GET operations.

        :param result: The result from the future instance. A dictionary with
            at least the `result` key.
        """
        result['result'] = dumps(result['result'])
        result['code'] = 200

        self.set_status(200)
        self.write(result)
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

        return valid_content

    @protected("POST")
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

        if not self._has_valid_content_type():
            return_code = 415

        return return_code

    def _post(self, json_obj):
        """Placeholder method - used internally.

        This is called by the actual method that implements POST request.
        Subclasses should provide their own implementation.

        This will return a status code of 501.

        :param json_obj: A JSON object.
        """
        self.write_error(status_code=501)

    @protected("DELETE")
    @asynchronous
    def delete(self, *args, **kwargs):
        if kwargs and kwargs.get('id', None):
            self._delete(kwargs['id'])
        else:
            self.write_error(status_code=400)

    def _delete(self, doc_id):
        """Placeholder method - used internally.

        This is called by the actual method that implements DELETE request.
        Subclasses should provide their own implementation.

        This will return a status code of 501.

        :param doc_id: The ID of the documento to delete.
        """
        self.write_error(status_code=501)

    @protected("GET")
    @asynchronous
    def get(self, *args, **kwargs):
        if kwargs and kwargs.get('id', None):
            self.executor.submit(
                partial(self._get_one, kwargs['id'])
            ).add_done_callback(
                lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._create_valid_response, future.result())
                )
            )
        else:
            self.executor.submit(
                partial(self._get, **kwargs)
            ).add_done_callback(
                lambda future:
                tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._get_callback, future.result()))
            )

    def _get_one(self, doc_id):
        """Get just one single document from the collection.

        :return The result from the database.
        """
        return find_one(
            self.collection, doc_id, fields=self._get_query_fields()
        )

    def _get(self, **kwargs):
        """Method called by the real GET one.

        For special uses, sublcasses should override this one and provide
        their own implementation.

        By default it executes a search on all the documents in a collection,
        returnig all the documents found.

        It should return a dictionary with at least the following fields:
        `result` - that will hold the actual operation result
        `count` - the total number of results available
        `limit` - how many results have been collected
        """
        skip, limit = self._get_skip_and_limit()
        spec, sort, fields = self._get_query_args()

        unique = self.get_query_argument(AGGREGATE_KEY, default=None)
        if unique:
            self.log.info("Performing aggregation on %s", unique)
            return aggregate(
                self.collection, unique, sort=sort, fields=fields, match=spec,
                limit=limit
            )
        else:
            return find_and_count(
                self.collection,
                limit,
                skip,
                spec=spec,
                fields=fields,
                sort=sort
            )

    def _get_skip_and_limit(self):
        """Retrieve the `skip` and `limit` query arguments.

        :return A tuple with the `skip` and `limit` arguments.
        """
        skip = 0
        limit = 0

        if self.request.arguments:
            skip = int(self.get_query_argument(SKIP_KEY, default=0))
            limit = int(self.get_query_argument(LIMIT_KEY, default=0))

        return skip, limit

    def _get_query_args(self):
        """Retrieve all the arguments from the query string.

        This method will return the `spec`, `sort` and `fields` data structures
        that can be used to perform MongoDB queries.

        :return A tuple with `spec`, `sort` and `fields` data structures.
        """
        spec = {}
        sort = None
        fields = None

        if self.request.arguments:
            spec = self._get_query_spec()
            sort = self._get_query_sort()
            fields = self._get_query_fields()

        return (spec, sort, fields)

    def _get_query_spec(self):
        """Get values from the query string to build a `spec` data structure.

        A `spec` data structure is a dictionary whose keys are the keys
        accepted by this handler GET method.

        :return A `spec` data structure.
        """
        spec = {
            k: v for k, v in [
                (key, val)
                for key in self._valid_keys('GET')
                for val in self.get_query_arguments(key)
                if val is not None
            ]
        }

        date_range = self.get_query_argument(DATE_RANGE_KEY, default=None)
        if date_range:
            # Today needs to be set at the end of the day!
            today = datetime.combine(
                date.today(), time(23, 59, 59, tzinfo=tz_util.utc)
            )
            previous = self._calculate_date_range(date_range)

            spec[CREATED_KEY] = {'$gte': previous, '$lt': today}

        return spec

    def _get_query_sort(self):
        """Get values from the query string to build a `sort` data structure.

        A `sort` data structure is a list of tuples in a `key-value` fashion.
        The keys are the values passed as the `sort` argument on the query,
        they values are based on the `sort_order` argument and defaults to the
        descending order.

        :return A `sort` data structure.
        """
        sort_fields = self.get_query_arguments(SORT_KEY)
        sort_order = int(
            self.get_query_argument(SORT_ORDER_KEY, default=DESCENDING)
        )

        # Wrong number for sort order? Force descending.
        if sort_order != ASCENDING and sort_order != DESCENDING:
            self.log.warn(
                "Wrong sort order used (%d), default to %d",
                sort_order, DESCENDING
            )
            sort_order = DESCENDING

        sort = None
        if sort_fields:
            sort = [
                (field, sort_order)
                for field in sort_fields
            ]

        return sort

    def _get_query_fields(self):
        """Get values from the query string to build a `fields` data structure.

        :return A `fields` data structure.
        """
        fields = None

        y_fields = self.get_query_arguments(FIELD_KEY)
        n_fields = self.get_query_arguments(NOT_FIELD_KEY)

        if y_fields and not n_fields:
            fields = list(set(y_fields))
        elif n_fields:
            fields = dict.fromkeys(list(set(y_fields)), True)
            fields.update(dict.fromkeys(list(set(n_fields)), False))

        return fields

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

    @staticmethod
    def _calculate_date_range(date_range):
        """Calculate the new date subtracting the passed number of days.

        It removes the passed days from today date, calculated at midnight
        UTC.

        :param date_range: The number of days to remove from today.
        :type date_range int, long, str
        :return A new `datetime.date` object that is the result of the
            subtraction of `datetime.date.today()` and
            `datetime.timedelta(days=date_range)`.
        """
        if isinstance(date_range, types.StringTypes):
            date_range = int(date_range)

        date_range = abs(date_range)
        if date_range > timedelta.max.days:
            date_range = DEFAULT_DATE_RANGE

        # Calcuate with midnight in mind though, so we get the starting of
        # the day for the previous date.
        today = datetime.combine(
            date.today(), time(tzinfo=tz_util.utc)
        )
        delta = timedelta(days=date_range)

        return today - delta
