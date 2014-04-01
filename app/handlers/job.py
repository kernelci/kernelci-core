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
from utils.db import save
from utils.docimport import import_job_from_json


class JobHandler(BaseHandler):
    """Handle the /job URLs."""

    @property
    def collection(self):
        return self.db[JOB_COLLECTION]

    @property
    def accepted_keys(self):
        return ('job', 'kernel')

    @asynchronous
    def post(self, *args, **kwargs):
        if self.request.headers['Content-Type'] != self.accepted_content_type:
            self.send_error(status_code=415)
        else:
            json_obj = json.loads(self.request.body.decode('utf8'))
            if self.is_valid_put(json_obj):

                self.executor.submit(
                    partial(self._import, json_obj)
                ).add_done_callback(
                    lambda future:
                    tornado.ioloop.IOLoop.instance().add_callback(
                        partial(self._post_callback, future.result()))
                )

            else:
                self.send_error(status_code=400)

    def _import(self, json_obj):
        """Internal function to handle jobs import.

        Should be run on a separate thread.

        :param json_obj: The JSON-like object with the information.
        """
        response = import_job_from_json(json_obj)

        if response:
            result = save(self.db, response)

        return result
