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

import tornado

from functools import partial
from tornado.web import (
    asynchronous,
)

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
from handlers.base import BaseHandler
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


class CountHandler(BaseHandler):
    """Handle the /count URLs."""

    def __init__(self, application, request, **kwargs):
        super(CountHandler, self).__init__(application, request, **kwargs)

        # Internally used only. It is used to retrieve just one field for
        # the query results since we only need to count the results, we are
        # not interested in the values.
        self._fields = {ID_KEY: True}

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

    @asynchronous
    def get(self, *args, **kwargs):
        if kwargs and kwargs.get('collection', None):
            if kwargs['collection'] in COLLECTIONS.keys():
                self.executor.submit(
                    partial(self._count_one_collection, kwargs['collection'])
                ).add_done_callback(
                    lambda future:
                    tornado.ioloop.IOLoop.instance().add_callback(
                        partial(
                            self._get_callback, future.result()
                        )
                    )
                )
            else:
                self.write_error(404)
        else:
            self.executor.submit(
                partial(self._count_all_collections)
            ).add_done_callback(
                lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._get_callback, future.result())
                )
            )

    def _count_one_collection(self, collection):
        """Count all the available documents in the provide collection.

        :param collection: The collection whose elements should be counted.
        :return A dictionary with the `result` field that contains a dictionary
            with the fields `collection` and `count`.
        """
        result = {}
        spec = self._get_query_spec()

        if spec:
            number = find_and_count(
                self.db[COLLECTIONS[collection]], 0, 0, spec, self._fields
            )
            if number:
                number = number['count']
            else:
                number = 0
            result['result'] = dict(
                collection=collection, count=number, fields=spec
            )
        else:
            result['result'] = dict(
                collection=collection,
                count=count(self.db[COLLECTIONS[collection]])
            )

        return result

    def _count_all_collections(self):
        """Count all the available documents in the database collections.

        :return A dictionary with the `result` field that contains a list of
            dictionaries with the fields `collection` and `count`.
        """
        result = dict(result=[])

        spec = self._get_query_spec()
        if spec:
            for key, val in COLLECTIONS.iteritems():
                number = find_and_count(self.db[val], 0, 0, spec, self._fields)
                if number:
                    number = number['count']
                else:
                    number = 0
                result['result'].append(
                    dict(collection=key, count=number))
        else:
            for key, val in COLLECTIONS.iteritems():
                result['result'].append(
                    dict(collection=key, count=count(self.db[val]))
                )

        return result

    @asynchronous
    def post(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)

    @asynchronous
    def delete(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(status_code=501)
