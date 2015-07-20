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

"""Base module for testing all handlers."""

import concurrent.futures
import mock
import mongomock
import random
import string
import tornado

from tornado.testing import (
    AsyncHTTPTestCase,
    LogTrapTestCase
)

import handlers.app
import models.token as mtoken


class TestHandlerBase(AsyncHTTPTestCase, LogTrapTestCase):

    def setUp(self):
        # Default Content-Type header returned by Tornado.
        self.content_type = "application/json; charset=UTF-8"
        self.req_token = mtoken.Token()
        self.database = mongomock.Connection()["kernel-ci"]
        self.dboptions = {
            "dbpassword": "",
            "dbuser": ""
        }
        self.mailoptions = {}
        self.settings = {
            "dboptions": self.dboptions,
            "database": self.database,
            "executor": concurrent.futures.ThreadPoolExecutor(max_workers=1),
            "default_handler_class": handlers.app.AppHandler,
            "debug": False,
            "version": "foo",
            "master_key": "bar",
            "mailoptions": self.mailoptions,
            "senddelay": 60*60
        }

        super(TestHandlerBase, self).setUp()

        patched_find_token = mock.patch(
            "handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = self.req_token

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = (True, self.req_token)

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)

        self.doc_id = "".join(
            [random.choice(string.digits) for x in xrange(24)])

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()
