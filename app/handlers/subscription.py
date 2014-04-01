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
from models.job import JOB_COLLECTION
from models.subscription import (
    SUBSCRIPTION_COLLECTION,
    SubscriptionDocument,
)
from utils.db import (
    find_one,
    save,
)


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
                    partial(self._subscribe, json_obj)
                ).add_done_callback(
                    lambda future:
                    tornado.ioloop.IOLoop.instance().add_callback(
                        partial(self._post_callback, future.result()))
                )

            else:
                self.send_error(status_code=400)

    def _subscribe(self, json_obj):
        """Internal function to handle subscriptions.

        Should be run on a separate thread.

        :param json_obj: The JSON-like object with all the information.
        """
        job_id = json_obj['job']
        email = json_obj['email']

        job_doc = find_one(self.db[JOB_COLLECTION], job_id)

        if job_doc:
            subscription = find_one(self.collection, job_id, 'job_id')

            if subscription:
                sub_doc = SubscriptionDocument.from_json(subscription)
                sub_doc.emails = email
            else:
                sub_id = SubscriptionDocument.SUBSCRIPTION_ID_FORMAT % job_id
                sub_doc = SubscriptionDocument(sub_id, job_id, email)

            return save(self.db, sub_doc)
        else:
            return 404

    def delete(self, *args, **kwargs):
        self.write_error(status_code=501)
