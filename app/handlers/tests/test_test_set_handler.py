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

import json
import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestTestSetHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._TEST_SET_URL], **self.settings)

    @mock.patch("utils.db.find_and_count")
    def test_get(self, mock_find):
        mock_find.return_value = ([{"foo": "bar"}], 1)

        headers = {"Authorization": "foo"}
        response = self.fetch("/test/set/", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

    def test_post_without_token(self):
        body = json.dumps(dict(name="set", version="1.0"))

        response = self.fetch("/test/set", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/set", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/set", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_correct_with_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(name="test-set", test_suite_id="test-suite", version="1.0"))

        response = self.fetch(
            "/test/set/fake-id", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_with_error(self, mock_id, mock_find, mock_save):
        mock_id.return_value = "suite-id"
        mock_find.return_value = {"_id": "suite-id"}
        mock_save.return_value = (500, None)
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test-set", test_suite_id="suite-id", version="1.0"))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct(self, mock_id, mock_find, mock_save):
        mock_id.return_value = "suite-id"
        mock_find.return_value = {"_id": "suite-id", "name": "suite-name"}
        mock_save.return_value = (201, "test-set-id")
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="test", test_suite_id="test-suite", version="1.0",))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.test.import_test_cases_from_test_set")
    @mock.patch("utils.db.save")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_with_test_case(
            self, mock_id, mock_find, mock_save, mock_task):
        mock_id.return_value = "suite-id"
        mock_find.return_value = {"_id": "suite-id", "name": "test-suite"}
        mock_save.return_value = (201, "test-set-id")
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-set",
                test_suite_id="suite-id",
                version="1.0", test_case=[{"foo": "bar"}]
            )
        )

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_correct_with_wrong_test_suite_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(name="test-set", test_suite_id="suite-id", version="1.0"))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_post_correct_with_wrong_test_case(
            self, mock_id, mock_find, mock_save):
        mock_id.return_value = "test-suite"
        mock_find.return_value = {"_id": "test-suite", "name": "suite-name"}
        mock_save.return_value = (201, "doc-id")
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-set",
                test_suite_id="test-suite",
                version="1.0", test_case={"foo": "bar"}
            )
        )

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_correct_with_params_error(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                name="test-set",
                test_suite_id="test-suite",
                version="1.0", parameters=[{"foo": "bar"}]))

        response = self.fetch(
            "/test/set", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_token(self):
        response = self.fetch("/test/set/id", method="DELETE")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_wrong_token(self):
        headers = {"Authorization": "foo"}
        self.validate_token.return_value = (False, None)

        response = self.fetch(
            "/test/set/id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_wrong_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/wrong-id", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

    def test_put_no_token(self):
        response = self.fetch("/test/set/id", method="PUT", body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_wrong_token(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        self.validate_token.return_value = (False, None)

        response = self.fetch(
            "/test/set/id", method="PUT", headers=headers, body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/test/set/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/set/", method="PUT", headers=headers, body=""
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_valid_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/test/set/id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_json_data(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/test/set/id", method="PUT", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_valid_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/set/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    def test_put_id_not_found(self, mock_id, mock_find):
        mock_id.return_value = "fake-id"
        mock_find.return_value = None

        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="set", parameters={"foo": "bar"}))

        response = self.fetch(
            "/test/set/wrong-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

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
            "/test/set/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

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
            "/test/set/fake-id", method="PUT", body=body, headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
