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

"""Test module for the TestSetHandler handler."""

import concurrent.futures
import json
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestTestSetHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestTestSetHandler, self).setUp()

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
            "mailoptions": mailoptions,
            "senddelay": 5,
            "client": self.mongodb_client,
            "executor": concurrent.futures.ThreadPoolExecutor(max_workers=2),
            "default_handler_class": handlers.app.AppHandler,
            "debug": False
        }

        return tornado.web.Application([urls._TEST_SET_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    @mock.patch("utils.db.find_and_count")
    def test_get(self, mock_find):
        mock_find.return_value = ([{"foo": "bar"}], 1)

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/set/", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_set.TestSetHandler.collection")
    def test_get_by_id_not_found(self, collection, mock_id):
        mock_id.return_value = "suite-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = None

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/set/set-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_set.TestSetHandler.collection")
    def test_get_by_id_not_found_empty_list(self, collection, mock_id):
        mock_id.return_value = "set-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/set/set-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_set.TestSetHandler.collection")
    def test_get_by_id_found(self, collection, mock_id):
        mock_id.return_value = "set-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = {"_id": "set-id"}

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/set/set-id", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_without_token(self):
        body = json.dumps(dict(name="set", version="1.0"))

        response = self.fetch("/test/set", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/set", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/set", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_correct_with_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(name="test-set", test_suite_id="test-suite", version="1.0"))

        response = self.fetch(
            "/test/set/fake-id", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.save")
    def test_post_correct_with_error(self, mock_save):
        mock_save.return_value = (500, None)
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test-set", test_suite_id="test-suite", version="1.0"))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.save")
    def test_post_correct(self, mock_save):
        mock_save.return_value = (201, "test-set-id")
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test", test_suite_id="test-suite", version="1.0",))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_correct_with_test_case(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-set",
                test_suite_id="test-suite",
                version="1.0", test_case=[{"foo": "bar"}]
            )
        )

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch("/test/set/id", method="DELETE")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_wrong_token(self):
        headers = {"Authorization": "foo"}
        self.validate_token.return_value = False

        response = self.fetch(
            "/test/set/id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_wrong_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/wrong-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct_not_found(self, mock_id, mock_find):
        mock_id.return_value = "fake-id"
        mock_find.return_value = None
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct_with_error(self, mock_id, mock_find, mock_delete):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id"}
        mock_delete.return_value = 500
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_correct(self, mock_id, mock_find, mock_delete):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id"}
        mock_delete.side_effect = [200, 500]
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
