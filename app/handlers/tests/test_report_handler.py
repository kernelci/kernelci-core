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

"""Test module for the ReportHandler."""

import mock
import mongomock

from concurrent.futures import ThreadPoolExecutor
from tornado import (
    ioloop,
    testing,
    web,
)

from handlers.app import AppHandler
from urls import _REPORT_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestRerportHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestRerportHandler, self).setUp()

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

        settings = {
            "dboptions": dboptions,
            "client": self.mongodb_client,
            "executor": ThreadPoolExecutor(max_workers=2),
            "default_handler_class": AppHandler,
            "master_key": "bar",
            "debug": False,
        }

        return web.Application([_REPORT_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_post(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 501)

    def test_post_no_token(self):
        response = self.fetch("/reports", method="POST", body="")
        self.assertEqual(response.code, 403)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)

    def test_delete_no_token(self):
        response = self.fetch("/reports", method="DELETE")
        self.assertEqual(response.code, 403)

    def test_get_no_token(self):
        response = self.fetch("/reports")
        self.assertEqual(response.code, 403)

    @mock.patch("utils.db.find")
    @mock.patch("utils.db.count")
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch("/reports", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find")
    @mock.patch("utils.db.count")
    def test_get_with_keys(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports?job=job&kernel=kernel", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
