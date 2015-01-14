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

"""Test module for the TokenHandler handler."""

import json
import mock
import mongomock

from concurrent.futures import ThreadPoolExecutor
from tornado import (
    ioloop,
    testing,
    web,
)

from handlers.app import AppHandler
from urls import _SEND_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestSendHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestSendHandler, self).setUp()

        patched_find_token = mock.patch(
            "handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = True

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)

    def get_app(self):
        dboptions = {
            "dbpassword": "",
            "dbuser": ""
        }

        mailoptions = {}

        settings = {
            "dboptions": dboptions,
            "client": self.mongodb_client,
            "executor": ThreadPoolExecutor(max_workers=2),
            "default_handler_class": AppHandler,
            "master_key": "bar",
            "debug": False,
            "mailoptions": mailoptions,
            "senddelay": 60*60
        }

        return web.Application([_SEND_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_get(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="GET", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_no_token(self):
        response = self.fetch("/send", method="GET")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch("/send", method="DELETE")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_no_token(self):
        response = self.fetch("/send", method="POST", body="")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_missing_job_key(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        body = json.dumps(dict(kernel="kernel"))
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_missing_kernel_key(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        body = json.dumps(dict(job="job"))
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("taskqueue.tasks.schedule_boot_report")
    def test_post_correct(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        body = json.dumps(dict(job="job", kernel="kernel", delay=None))
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
