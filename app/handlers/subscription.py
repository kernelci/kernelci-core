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
from tornado.web import asynchronous

from handlers.base import BaseHandler
from models.subscription import SUBSCRIPTION_COLLECTION
from utils.subscription import subscribe


class SubscriptionHandler(BaseHandler):
    """Handle the /subscription URLs."""

    @property
    def collection(self):
        return self.db[SUBSCRIPTION_COLLECTION]

    @property
    def accepted_keys(self):
        return ('job', 'email')

    @asynchronous
    def post(self, *args, **kwargs):
        if self.request.headers['Content-Type'] != self.accepted_content_type:
            self.send_error(status_code=415)
        else:
            json_obj = json.loads(self.request.body.decode('utf8'))
            if self.is_valid_put(json_obj):

                self.executor.submit(
                    partial(subscribe, json_obj, self.db)
                ).add_done_callback(
                    lambda future:
                    tornado.ioloop.IOLoop.instance().add_callback(
                        partial(self._post_callback, future.result()))
                )

            else:
                self.send_error(status_code=400)

    def delete(self, *args, **kwargs):
        self.write_error(status_code=501)
