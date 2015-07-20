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

"""Test module for the CountHandler handler."""

import concurrent.futures
import json
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestCountHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.database = mongomock.Connection()["kernel-ci"]

        super(TestCountHandler, self).setUp()

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

        settings = {
            "dboptions": dboptions,
            "database": self.database,
            "executor": concurrent.futures.ThreadPoolExecutor(max_workers=1),
            "default_handler_class": handlers.app.AppHandler,
            "debug": False,
        }

        return tornado.web.Application([urls._COUNT_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_post(self):
        body = json.dumps(dict(job="job", kernel="kernel"))

        response = self.fetch("/count", method="POST", body=body)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        response = self.fetch("/count", method="DELETE")

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_wrong_resource(self):
        headers = {"Authorization": "foo"}

        response = self.fetch("/count/foobar", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_count_all(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/count", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_count_all_with_query(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/count?board=foo&status=FAIL", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_count_collection(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/count/boot", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_count_collection_with_query(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/count/boot?board=foo", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
