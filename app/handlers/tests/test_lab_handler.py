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

"""Test module for the LabHandler handler."""

import json
import mock
import tornado

import urls
import handlers.response

from handlers.tests.test_handler_base import TestHandlerBase


class TestLabHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._LAB_URL], **self.settings)

    def test_post_no_json(self):
        body = json.dumps(dict(name="name", contact={}))
        response = self.fetch("/lab", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch("/lab", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/lab", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json_no_fields(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="foo", contact={}))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json_no_all_fields(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="foo", contact={"name": "bar", "surname": "foo"}))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_with_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="foo", contact={"name": "bar", "surname": "foo"}))

        response = self.fetch(
            "/lab/lab-id", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("handlers.common.lab.create_lab")
    def test_post_correct_ok(self, mock_create_lab):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
            )
        )
        handler_response = handlers.response.HandlerResponse(201)
        handler_response.headers = {
            "Location": "lab-id"
        }
        mock_create_lab.return_value = handler_response

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        self.assertIsNotNone(response.headers["Location"])

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_get_by_id_not_found(self, find_one, mock_id):
        mock_id.return_value = "lab-01"
        find_one.side_effect = [None]

        headers = {"Authorization": "foo"}
        response = self.fetch("/lab/lab-01", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one2")
    def test_get_by_id_found(self, find_one, mock_id):
        find_one.side_effect = [{"_id": "foo", "name": "lab-01"}]
        mock_id.return_value = "lab-01"

        expected_body = (
            '{"code":200,"result":[{"_id":"foo","name":"lab-01"}]}'
        )

        headers = {"Authorization": "foo"}
        response = self.fetch("/lab/lab-01", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        self.assertEqual(response.body, expected_body)

    def test_delete_no_token(self):
        self.find_token.return_value = None

        response = self.fetch("/lab/lab", method="DELETE")
        self.assertEqual(response.code, 403)

    @mock.patch("utils.db.find_one2")
    def test_delete_with_token_no_lab(self, mock_find):
        mock_find.return_value = None
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    def test_delete_with_token(self, mock_find, mock_delete):
        mock_delete.return_value = 200
        mock_find.return_value = {
            "_id": self.doc_id,
            "token": "token"
        }

        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    def test_delete_with_token_error_delete(self, mock_find, mock_delete):
        mock_delete.return_value = 500
        mock_find.return_value = {
            "_id": self.doc_id,
            "token": "token"
        }

        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    @mock.patch("utils.db.find_one2")
    def test_delete_with_token_error_delete_token(
            self, mock_find, mock_delete):
        mock_delete.side_effect = [200, 500]
        mock_find.return_value = {
            "_id": self.doc_id,
            "token": "token"
        }

        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch("/lab", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_wrong_id(self):
        headers = {"Authorization": "foo"}

        response = self.fetch("/lab/foobar", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_no_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps({"name": "foo"})

        response = self.fetch("/lab", method="PUT", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_with_wrong_id(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps({"name": "foo"})

        response = self.fetch(
            "/lab/id", method="PUT", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_with_id_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch(
            "/lab/" + self.doc_id, method="PUT", headers=headers, body="foo")

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_wrong_content(self):
        headers = {"Authorization": "foo"}
        body = json.dumps({"name": "foo"})

        response = self.fetch(
            "/lab/" + self.doc_id, method="PUT", headers=headers, body=body)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("handlers.common.lab.update_lab")
    def test_put_correct(self, mock_update):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps({
            "name": "new-lab"
        })
        mock_update.return_value = handlers.response.HandlerResponse(200)

        response = self.fetch(
            "/lab/" + self.doc_id, method="PUT", headers=headers, body=body)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_put_json_not_valid(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps({
            "foo": "new-lab"
        })

        response = self.fetch(
            "/lab/" + self.doc_id, method="PUT", headers=headers, body=body)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
