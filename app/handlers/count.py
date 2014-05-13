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

from handlers.base import BaseHandler
from models.boot import BOOT_COLLECTION
from models.defconfig import DEFCONFIG_COLLECTION
from models.job import JOB_COLLECTION
from models.subscription import SUBSCRIPTION_COLLECTION
from utils.db import count

# All the available collections as key-value. The key is the same used for the
# URL configuration.
COLLECTIONS = {
    'boot': BOOT_COLLECTION,
    'defconfig': DEFCONFIG_COLLECTION,
    'job': JOB_COLLECTION,
    'subscription': SUBSCRIPTION_COLLECTION,
}


class CountHandler(BaseHandler):
    """Handle the /count URLs."""

    def __init__(self, application, request, **kwargs):
        super(CountHandler, self).__init__(application, request, **kwargs)

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
                            self._create_valid_response, future.result()
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
        pass

    def _count_all_collections(self):
        result = dict(result=[])

        for key, val in COLLECTIONS.iteritems():
            result['result'].append(
                dict(collection=key, count=count(self.db[val]))
            )

        return result
