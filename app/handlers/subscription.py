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

"""The RequetHandler for /subscription URLs."""

import json

from handlers.base import BaseHandler
from handlers.response import HandlerResponse
from handlers.common import SUBSCRIPTION_VALID_KEYS
from models import (
    EMAIL_KEY,
    SUBSCRIPTION_COLLECTION,
)
from utils.subscription import (
    subscribe,
    unsubscribe,
)
from utils.validator import is_valid_json
from utils.db import delete


class SubscriptionHandler(BaseHandler):
    """Handle the /subscription URLs."""

    def __init__(self, application, request, **kwargs):
        super(SubscriptionHandler, self).__init__(
            application, request, **kwargs
        )

    @property
    def collection(self):
        return self.db[SUBSCRIPTION_COLLECTION]

    def _valid_keys(self, method):
        return SUBSCRIPTION_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = HandlerResponse()

        response.status_code = subscribe(self.db, kwargs['json_obj'])
        response.result = None
        response.reason = self._get_status_message(response.status_code)

        return response

    def _delete(self, doc_id):
        response = HandlerResponse()
        response.result = None

        if self.request.body:
            try:
                json_obj = json.loads(self.request.body.decode('utf8'))

                if is_valid_json(json_obj, self._valid_keys('DELETE')):
                    response.status_code = unsubscribe(
                        self.collection, doc_id, json_obj[EMAIL_KEY]
                    )
                else:
                    response.status_code = 400

                response.reason = self._get_status_message(
                    response.status_code
                )
            except ValueError:
                response.status_code = 420
                response.reason = "No JSON data found in the DELETE request"
        else:
            response.status_code = delete(self.collection, doc_id)
            if response.status_code == 200:
                response.reason = (
                    "Subscriptsions for resource %s deleted" % doc_id
                )

        return response
