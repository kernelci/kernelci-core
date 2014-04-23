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
import tornado

from functools import partial

from handlers.base import BaseHandler
from models.subscription import SUBSCRIPTION_COLLECTION
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
        valid_keys = {
            'GET': ['job'],
            'POST': ['job', 'email'],
            'DELETE': ['email'],
        }

        return valid_keys.get(method, None)

    def _post(self, json_obj):
        self.executor.submit(
            partial(subscribe, self.db, json_obj)).add_done_callback(
                lambda future:
                tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._create_valid_response, future.result()))
            )

    def _delete(self, doc_id):
        if self.request.body:
            try:
                json_obj = json.loads(self.request.body.decode('utf8'))

                if is_valid_json(json_obj, self._valid_keys('DELETE')):
                    self._delete_email_or_doc(
                        unsubscribe,
                        self.collection,
                        doc_id,
                        json_obj['email']
                    )
                else:
                    self.send_error(status_code=400)
            except ValueError:
                self.log.error("No JSON data found in the DELETE request")
                self.write_error(status_code=420)
        else:
            self._delete_email_or_doc(delete, self.collection, doc_id)

    def _delete_email_or_doc(self, func, *args):
        self.executor.submit(
            partial(
                func,
                *args
            )
        ).add_done_callback(
            lambda future:
            tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result()))
        )
