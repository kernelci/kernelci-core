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

"""The RequestHandler for /boot URLs."""

from handlers.base import BaseHandler
from handlers.response import HandlerResponse
from models import (
    CREATED_KEY,
    DEFCONFIG_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    STATUS_KEY,
    TIME_KEY,
    WARNINGS_KEY,
)
from models.boot import BOOT_COLLECTION
from taskqueue.tasks import import_boot


class BootHandler(BaseHandler):
    """Handle the /boot URLs."""

    def __init__(self, application, request, **kwargs):
        super(BootHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[BOOT_COLLECTION]

    def _valid_keys(self, method):
        valid_keys = {
            'POST': [JOB_KEY, KERNEL_KEY],
            'GET': [
                CREATED_KEY, WARNINGS_KEY, JOB_ID_KEY,
                JOB_KEY, KERNEL_KEY, DEFCONFIG_KEY, TIME_KEY, STATUS_KEY,
            ]
        }

        return valid_keys.get(method, None)

    def _post(self, json_obj):
        response = HandlerResponse(202)
        response.reason = "Request accepted and being imported"
        response.result = None

        import_boot.apply_async([json_obj])

        return response
