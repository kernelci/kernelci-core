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

"""Test module for the TestCaseHandler handler."""

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


class TestTestCaseHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestTestCaseHandler, self).setUp()

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

        return tornado.web.Application([urls._TEST_CASE_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    @mock.patch("utils.db.find_and_count")
    def test_get(self, mock_find):
        mock_find.return_value = ([{"foo": "bar"}], 1)

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/case/", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_case.TestCaseHandler.collection")
    def test_get_by_id_not_found(self, collection, mock_id):
        mock_id.return_value = "suite-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = None

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/case/case-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_case.TestCaseHandler.collection")
    def test_get_by_id_not_found_empty_list(self, collection, mock_id):
        mock_id.return_value = "case-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/case/case-id", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("handlers.test_case.TestCaseHandler.collection")
    def test_get_by_id_found(self, collection, mock_id):
        mock_id.return_value = "case-id"
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = {"_id": "case-id"}

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/case/case-id", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_without_token(self):
        body = json.dumps(dict(name="set", version="1.0"))

        response = self.fetch("/test/case", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/case", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/case", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/case", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_correct_with_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(name="test-set", test_suite_id="test-suite", version="1.0"))

        response = self.fetch(
            "/test/case/fake-id", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.save")
    def test_post_correct_with_error(self, mock_save, mock_id, mock_find):
        mock_save.return_value = (500, None)
        mock_id.return_value = "test-suite"
        mock_find.return_value = {"_id": "test-suite"}
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test-set", test_suite_id="test-suite", version="1.0"))

        response = self.fetch(
            "/test/case", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.save")
    def test_post_correct(self, mock_save, mock_id, mock_find):
        mock_save.return_value = (201, "test-case-id")
        mock_id.return_value = "test-suite"
        mock_find.return_value = {"_id": "test-suite"}
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test", test_suite_id="test-suite", version="1.0",))

        response = self.fetch(
            "/test/case", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.save")
    def test_post_correct_with_params(self, mock_save, mock_id, mock_find):
        mock_save.return_value = (201, "test-case-id")
        mock_id.return_value = "test-suite"
        mock_find.return_value = {"_id": "test-suite"}
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-case",
                test_suite_id="test-suite",
                version="1.0", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/case", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_correct_with_params_error(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-case",
                test_suite_id="test-suite",
                version="1.0", parameters=[{"foo": "bar"}]))

        response = self.fetch(
            "/test/case", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_with_wrong_test_suite_id(self, mock_id, mock_find):
        mock_id.return_value = "test-suite"
        mock_find.return_value = None
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-case",
                test_suite_id="test-suite",
                version="1.0", parameters=[{"foo": "bar"}]))

        response = self.fetch(
            "/test/case", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch("/test/case/id", method="DELETE")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_wrong_token(self):
        headers = {"Authorization": "foo"}
        self.validate_token.return_value = False

        response = self.fetch(
            "/test/case/id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/case/", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_wrong_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/case/wrong-id", method="DELETE", headers=headers)

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
            "/test/case/fake-id", method="DELETE", headers=headers)

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
            "/test/case/fake-id", method="DELETE", headers=headers)

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
            "/test/case/fake-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_no_token(self):
        response = self.fetch("/test/case/id", method="PUT", body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_wrong_token(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        self.validate_token.return_value = False

        response = self.fetch(
            "/test/case/id", method="PUT", headers=headers, body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/case/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_no_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/case/", method="PUT", headers=headers, body="")

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_no_valid_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/case/id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_no_json_data(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            "/test/case/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_put_no_valid_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/case/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_id_not_found(self, mock_id, mock_find):
        mock_id.return_value = "fake-id"
        mock_find.return_value = None

        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/case/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_valid_no_error(self, mock_id, mock_find, mock_update):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id", "name": "fake"}
        mock_update.return_value = 200
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/case/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_valid_with_error(self, mock_id, mock_find, mock_update):
        mock_id.return_value = "fake-id"
        mock_find.return_value = {"_id": "fake-id", "name": "bar"}
        mock_update.return_value = 500
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/case/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
