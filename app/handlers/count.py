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

"""Handle the /count URLs used to count objects in the database."""

from tornado.web import (
    asynchronous,
)

from handlers.base import BaseHandler
from handlers.common import (
    get_and_add_date_range,
    get_query_spec,
)
from handlers.response import HandlerResponse
from models import (
    ARCHITECTURE_KEY,
    BOARD_KEY,
    CREATED_KEY,
    DEFCONFIG_KEY,
    ERRORS_KEY,
    ID_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    PRIVATE_KEY,
    STATUS_KEY,
    TIME_KEY,
    WARNINGS_KEY,
)
from models.boot import BOOT_COLLECTION
from models.defconfig import DEFCONFIG_COLLECTION
from models.job import JOB_COLLECTION
from utils.db import (
    count,
    find_and_count,
)

# All the available collections as key-value. The key is the same used for the
# URL configuration.
COLLECTIONS = {
    'boot': BOOT_COLLECTION,
    'defconfig': DEFCONFIG_COLLECTION,
    'job': JOB_COLLECTION,
}

# This is a list of all the valid fields in the available models.
VALID_KEYS = {
    'GET': [
        ARCHITECTURE_KEY,
        BOARD_KEY,
        CREATED_KEY,
        DEFCONFIG_KEY,
        ERRORS_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        PRIVATE_KEY,
        STATUS_KEY,
        TIME_KEY,
        WARNINGS_KEY,
    ],
}

# Internally used only. It is used to retrieve just one field for
# the query results since we only need to count the results, we are
# not interested in the values.
COUNT_FIELDS = {ID_KEY: True}


class CountHandler(BaseHandler):
    """Handle the /count URLs."""

    def __init__(self, application, request, **kwargs):
        super(CountHandler, self).__init__(application, request, **kwargs)

    def _valid_keys(self, method):
        return VALID_KEYS.get(method, None)

    def _get_one(self, collection):
        response = HandlerResponse()

        if collection in COLLECTIONS.keys():
            response.result = count_one_collection(
                self.db[COLLECTIONS[collection]],
                collection,
                self.get_query_arguments,
                self._valid_keys("GET")
            )
        else:
            response.status_code = 404
            response.reason = "Collection %s not found" % collection
            response.result = None

        return response

    def _get(self, **kwargs):
        response = HandlerResponse()
        response.result = count_all_collections(
            self.db,
            self.get_query_arguments,
            self._valid_keys("GET")
        )

        return response

    @asynchronous
    def post(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)

    @asynchronous
    def delete(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)


def count_one_collection(
        collection, collection_name, query_args_func, valid_keys):
    """Count all the available documents in the provide collection.

    :param collection: The collection whose elements should be counted.
    :param collection_name: The name of the collection to count.
    :type collection_name: str
    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: A list containing the valid keys that should be
    retrieved.
    :type valid_keys: list
    :return A list containing a dictionary with the `collection`, `count` and
    optionally the `fields` fields.
    """
    result = []
    spec = get_query_spec(query_args_func, valid_keys)
    spec = get_and_add_date_range(spec, query_args_func)

    if spec:
        _, number = find_and_count(
            collection, 0, 0, spec, COUNT_FIELDS
        )
        if not number:
            number = 0

        result.append(
            dict(collection=collection_name, count=number, fields=spec)
        )
    else:
        result.append(
            dict(
                collection=collection_name,
                count=count(collection)
            )
        )

    return result


def count_all_collections(database, query_args_func, valid_keys):
    """Count all the available documents in the database collections.

    :param database: The datase connection to use.
    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: A list containing the valid keys that should be
    retrieved.
    :type valid_keys: list
    :return A list containing a dictionary with the `collection` and `count`
    fields.
    """
    result = []

    spec = get_query_spec(query_args_func, valid_keys)
    spec = get_and_add_date_range(spec, query_args_func)

    if spec:
        for key, val in COLLECTIONS.iteritems():
            _, number = find_and_count(
                database[val], 0, 0, spec, COUNT_FIELDS
            )
            if not number:
                number = 0
            result.append(dict(collection=key, count=number))
    else:
        for key, val in COLLECTIONS.iteritems():
            result.append(dict(collection=key, count=count(database[val])))

    return result
