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

from tornado import gen
from tornado.web import asynchronous

from base import BaseHandler
from models import JOB_COLLECTION
from utils import import_job_from_json


class JobHandler(BaseHandler):
    """Handle the /job URLs."""

    @property
    def collection(self):
        return self.db[JOB_COLLECTION]

    @property
    def accepted_keys(self):
        return ('job', 'kernel')

    @asynchronous
    @gen.engine
    def post(self, *args, **kwargs):
        if self.request.headers['Content-Type'] != self.accepted_content_type:
            self.send_error(status_code=415)
        else:
            json_doc = json.loads(self.request.body.decode('utf8'))
            if self.is_valid_put(json_doc):
                response = yield gen.Task(
                    import_job_from_json,
                    json_doc,
                    self.db
                )

                self.write(response)
                self.finish()
            else:
                self.send_error(status_code=400)
