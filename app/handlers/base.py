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

import tornado.web

from bson.json_util import dumps
from tornado import gen
from tornado.web import asynchronous

from models import DB_NAME
from utils import is_valid_json_put
from utils.db import find_one_async, find_async

# Default and maximum limit for how many results to get back from the db.
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class BaseHandler(tornado.web.RequestHandler):

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

    def get_error_message(self, code):
        """Get custom error message based on the status code.

        :param code: The status code to get the message of.
        :type int
        :return The error message string, or None if the code does not have
                a custom message.
        """
        error_messages = {
            415: (
                'Please use "%s" as the default media type.' %
                self.accepted_content_type
            ),
            400: 'Provided JSON is not valid.',
        }

        return error_messages.get(code, None)

    @property
    def accepted_content_type(self):
        """The accepted Content-Type for PUT requests.

        Defaults to 'application/json'.
        """
        return 'application/json'

    def is_valid_put(self, json_obj):
        """Validate PUT requests content.

        :param json_obj: The JSON object to validate.
        :return True or False.
        """
        return is_valid_json_put(json_obj, self.accepted_keys)

    @asynchronous
    @gen.engine
    def get(self, *args, **kwargs):
        if kwargs and kwargs['id']:
            result = yield gen.Task(
                find_one_async,
                self.collection,
                kwargs['id'],
            )
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

        self.finish(dumps(result))

    def write_error(self, status_code, **kwargs):
        error_msg = self.get_error_message(status_code)
        if error_msg:
            self.finish(
                "<html><title>%(code)s: %(default_msg)s</title>"
                "<body>%(error_msg)s</body></html>" % {
                    "code": status_code,
                    "default_msg": self._reason,
                    "error_msg": error_msg
                }
            )
        else:
            super(BaseHandler, self).write_error(status_code)
