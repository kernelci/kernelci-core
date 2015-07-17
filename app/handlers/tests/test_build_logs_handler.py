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

"""Test module for the BuildLogsHandler."""

try:
    import simplejson as json
except ImportError:
    import json

import bson

import concurrent.futures
import mock
import mongomock
import random
import string
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestBuildLogsHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestBuildLogsHandler, self).setUp()

        patched_find_token = mock.patch(
            "handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = (True, "token")

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)
        self.doc_id = "".join(
            [random.choice(string.digits) for x in xrange(24)])
        self.url_id = "/build/" + self.doc_id + "/logs/"
        self.url = "/build/logs"

    def get_app(self):
        dboptions = {"dbpassword": "", "dbuser": ""}
        mailoptions = {}

        settings = {
            "dboptions": dboptions,
            "mailoptions": mailoptions,
            "senddelay": 5,
            "client": self.mongodb_client,
            "executor": concurrent.futures.ThreadPoolExecutor(max_workers=2),
            "default_handler_class": handlers.app.AppHandler,
            "debug": False
        }

        return tornado.web.Application(
            [urls._BUILD_ID_LOGS_URL, urls._BUILD_LOGS_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_delete_not_implemented(self):
        response = self.fetch(self.url_id, method="DELETE")
        self.assertEqual(response.code, 501)

    def test_post_not_implemented(self):
        body = json.dumps({})
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            self.url_id, method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 501)

    def test_put_not_implemented(self):
        body = json.dumps({})
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            self.url_id, method="PUT", body=body, headers=headers)
        self.assertEqual(response.code, 501)

    def test_delete_not_implemented_no_id(self):
        response = self.fetch(self.url, method="DELETE")
        self.assertEqual(response.code, 501)

    def test_post_not_implemented_no_id(self):
        body = json.dumps({})
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            self.url, method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 501)

    def test_put_not_implemented_no_id(self):
        body = json.dumps({})
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            self.url, method="PUT", body=body, headers=headers)
        self.assertEqual(response.code, 501)

    def test_get_no_token(self):
        response = self.fetch(self.url_id, method="GET")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("handlers.base.BaseHandler.validate_req_token")
    def test_get_invalid_token(self, mock_validate):
        mock_validate.return_value = (False, None)
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    def test_get_not_found(self, mock_find):
        mock_find.return_value = None
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    def test_get_wrong_id(self, mock_id):
        mock_id.side_effect = bson.errors.InvalidId("Wrong")
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    def test_get_valid(self, mock_find):
        mock_find.return_value = {"_id": self.doc_id}
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_and_count")
    def test_get_valid_no_id(self, mock_find):
        mock_find.return_value = ({"_id": self.doc_id}, 1)
        headers = {"Authorization": "bar"}
        response = self.fetch(
            self.url + "?defconfig=foo", method="GET", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
