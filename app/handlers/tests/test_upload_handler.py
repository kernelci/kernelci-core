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

"""Test module for the UploadHandler."""

import mock
import mongomock

from concurrent.futures import ThreadPoolExecutor
from tornado import (
    ioloop,
    testing,
    web,
)

import handlers.app as happ
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestUploadHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.database = mongomock.Connection()["kernel-ci"]

        super(TestUploadHandler, self).setUp()

        patched_find_token = mock.patch(
            "handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = (True, "token")

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
            "database": self.database,
            "executor": ThreadPoolExecutor(max_workers=1),
            "default_handler_class": happ.AppHandler,
            "master_key": "bar",
            "debug": False,
            "mailoptions": mailoptions,
            "senddelay": 60*60
        }

        return web.Application([urls._UPLOAD_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_get(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/upload", method="GET", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_no_token(self):
        response = self.fetch("/upload", method="GET")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/upload", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch("/upload", method="DELETE")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_no_token(self):
        response = self.fetch("/upload", method="POST", body="")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_token_wrong_content(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/upload", method="POST", body="", headers=headers)
        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_token_missing_content(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "multipart/form-data"
        }
        response = self.fetch(
            "/upload", method="POST", body="", headers=headers)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
