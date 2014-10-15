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

from tornado.web import asynchronous

from handlers.base import BaseHandler
from handlers.common import DEFCONFIG_VALID_KEYS
from handlers.response import HandlerResponse
from models import DEFCONFIG_COLLECTION
from utils.db import delete


class DefConfHandler(BaseHandler):
    """Handle the /defconfig URLs."""

    def __init__(self, application, request, **kwargs):
        super(DefConfHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[DEFCONFIG_COLLECTION]

    def _valid_keys(self, method):
        return DEFCONFIG_VALID_KEYS.get(method, None)

    @asynchronous
    def post(self, *args, **kwargs):
        """Not implemented."""
        self.write_error(501)

    def _delete(self, defconf_id):
        response = HandlerResponse()
        response.result = None

        response.status_code = delete(self.collection, defconf_id)
        if response.status_code == 200:
            response.reason = "Resource '%s' deleted" % defconf_id

        return response
