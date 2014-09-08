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


# Internally used only. It is used to retrieve just one field for
# the query results since we only need to count the results, we are
# not interested in the values.
COUNT_FIELDS = {ID_KEY: True}


class CountHandler(BaseHandler):
    """Handle the /count URLs."""

    def __init__(self, application, request, **kwargs):
        super(CountHandler, self).__init__(application, request, **kwargs)

    def _valid_keys(self, method):
        valid_keys = {
            # This is a set of all the valid fields in the available models.
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

        return valid_keys.get(method, None)

    def _get_one(self, collection):
        response = HandlerResponse()

        if collection in COLLECTIONS.keys():
            response.result = self._count_one_collection(collection)
        else:
            response.status_code = 404
            response.reason = "Collection %s not found" % collection
            response.result = None

        return response

    def _get(self, **kwargs):
        response = HandlerResponse()
        response.result = self._count_all_collections()

        return response

    def _count_one_collection(self, collection):
        """Count all the available documents in the provide collection.

        :param collection: The collection whose elements should be counted.
        :return A dictionary with the `result` field that contains a dictionary
            with the fields `collection` and `count`.
        """
        result = []
        spec = self._get_query_spec()
        spec = self._get_and_add_date_range(spec)

        if spec:
            _, number = find_and_count(
                self.db[COLLECTIONS[collection]], 0, 0, spec, COUNT_FIELDS
            )
            if not number:
                number = 0

            result.append(
                dict(collection=collection, count=number, fields=spec)
            )
        else:
            result.append(
                dict(
                    collection=collection,
                    count=count(self.db[COLLECTIONS[collection]])
                )
            )

        return result

    def _count_all_collections(self):
        """Count all the available documents in the database collections.

        :return A dictionary with the `result` field that contains a list of
            dictionaries with the fields `collection` and `count`.
        """
        result = []

        spec = self._get_query_spec()
        spec = self._get_and_add_date_range(spec)
        if spec:
            for key, val in COLLECTIONS.iteritems():
                _, number = find_and_count(
                    self.db[val], 0, 0, spec, COUNT_FIELDS
                )
                if not number:
                    number = 0
                result.append(dict(collection=key, count=number))
        else:
            for key, val in COLLECTIONS.iteritems():
                result.append(dict(collection=key, count=count(self.db[val])))

        return result

    @asynchronous
    def post(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)

    @asynchronous
    def delete(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)
