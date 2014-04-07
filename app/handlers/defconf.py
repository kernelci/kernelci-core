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

"""The RequestHandler for /defconfig URLs."""

import tornado

from functools import partial

from handlers.base import BaseHandler
from models.defconfig import DEFCONFIG_COLLECTION
from utils.db import delete


class DefConfHandler(BaseHandler):
    """Handle the /defconfig URLs."""

    def __init__(self, application, request, **kwargs):
        super(DefConfHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[DEFCONFIG_COLLECTION]

    def _valid_keys(self, method):
        valid_keys = {
            'DELETE': ['defconf']
        }

        return valid_keys.get(method, None)

    def _delete(self, json_obj):
        self.executor.submit(
            partial(delete, json_obj['defconf'])
        ).add_done_callback(
            lambda future:
            tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result())
            )
        )
