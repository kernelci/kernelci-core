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
from handlers.common import (
    BOOT_VALID_KEYS,
    get_query_spec,
)
from handlers.response import HandlerResponse
from models import BOOT_COLLECTION
from taskqueue.tasks import import_boot
from utils.db import (
    delete,
    find_one,
)


class BootHandler(BaseHandler):
    """Handle the /boot URLs."""

    def __init__(self, application, request, **kwargs):
        super(BootHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[BOOT_COLLECTION]

    def _valid_keys(self, method):
        return BOOT_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = HandlerResponse(202)
        response.reason = "Request accepted and being imported"
        response.result = None

        import_boot.apply_async([kwargs['json_obj']])

        return response

    def execute_delete(self, *args, **kwargs):
        response = None

        if kwargs and kwargs.get('id', None):
            doc_id = kwargs['id']
            if find_one(self.collection, doc_id):
                response = self._delete(doc_id)
                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % doc_id
            else:
                response = HandlerResponse(404)
                response.reason = "Resource '%s' not found" % doc_id
        else:
            spec = get_query_spec(
                self.get_query_arguments, self._valid_keys("DELETE")
            )
            if spec:
                response = self._delete(spec)
                if response.status_code == 200:
                    response.reason = (
                        "Resources identified with '%s' deleted" % spec
                    )
            else:
                response = HandlerResponse(400)
                response.result = None
                response.reason = (
                    "No valid data provided to execute a DELETE"
                )

        return response

    def _delete(self, spec_or_id):
        response = HandlerResponse(200)
        response.result = None

        response.status_code = delete(self.collection, spec_or_id)
        response.reason = self._get_status_message(response.status_code)

        return response
