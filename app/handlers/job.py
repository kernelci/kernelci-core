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

"""The RequestHandler for /job URLs."""

import json
import tornado

from functools import partial
from tornado.web import asynchronous

from handlers.base import BaseHandler
from models.job import JOB_COLLECTION
from utils.db import delete
from taskqueue.tasks import send_emails, import_job


class JobHandler(BaseHandler):
    """Handle the /job URLs."""

    @property
    def collection(self):
        return self.db[JOB_COLLECTION]

    def _valid_keys(self, method):
        valid_keys = {
            'POST': ['job', 'kernel'],
            'DELETE': ['job'],
        }

        return valid_keys.get(method, None)

    @asynchronous
    def post(self, *args, **kwargs):

        self._check_content_type()

        json_obj = json.loads(self.request.body.decode('utf8'))
        if self._has_valid_keys(json_obj, self._valid_keys('POST')):
            import_job.apply_async([json_obj], link=send_emails.s())
            self._create_valid_response(200)
        else:
            self.send_error(status_code=400)

    @asynchronous
    def delete(self, *args, **kwargs):

        self._check_content_type()

        json_obj = json.loads(self.request.body.decode('utf8'))
        if self._has_valid_keys(json_obj, self._valid_keys('DELETE')):
            self.executor.submit(
                partial(delete, self.collection, json_obj['job'])
            ).add_done_callback(
                lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._create_valid_response, future.result())
                )
            )
        else:
            self.send_error(status_code=400)
