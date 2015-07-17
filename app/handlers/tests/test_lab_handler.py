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


class TestLabHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestLabHandler, self).setUp()

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
            "client": self.mongodb_client,
            "executor": concurrent.futures.ThreadPoolExecutor(max_workers=2),
            "default_handler_class": handlers.app.AppHandler,
            "debug": False
        }

        return tornado.web.Application([urls._LAB_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_post_no_json(self):
        body = json.dumps(dict(name="name", contact={}))
        response = self.fetch("/lab", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        response = self.fetch("/lab", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/lab", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json_no_fields(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(name="foo", contact={}))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json_no_all_fields(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(name="foo", contact={"name": "bar", "surname": "foo"}))

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one")
    def test_post_correct(self, find_one):
        find_one.side_effect = [None]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
            )
        )

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        self.assertIsNotNone(response.headers["Location"])

    @mock.patch("utils.db.find_one")
    def test_post_correct_lab_id_found(self, find_one):
        find_one.side_effect = [True]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
            )
        )

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_post_correct_with_id_lab_id_not_found(self, find_one, mock_id):
        mock_id.return_value = "lab-01"
        find_one.side_effect = [None]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
            )
        )

        response = self.fetch(
            "/lab/lab-01", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one")
    def test_post_correct_with_token_not_found(self, find_one):
        find_one.side_effect = [None, None]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
                token="token"
            )
        )

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("utils.db.find_one")
    def test_post_correct_with_token_found(self, find_one):
        token_json = {
            "_id": "token_id",
            "token": "token",
            "email": "foo",
            "username": "bar"
        }
        find_one.side_effect = [None, token_json, None]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
                token="token"
            )
        )

        response = self.fetch(
            "/lab", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        self.assertIsNotNone(response.headers["Location"])

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_post_correct_with_id_lab_id_found(self, find_one, mock_id):
        lab_json = {
            "name": "foo",
            "token": "token-id",
            "contact": {
                "name": "foo",
                "surname": "bar",
                "email": "foo"
            }
        }

        mock_id.return_value = "foo"
        find_one.side_effect = [lab_json]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
                address={"street_1": "foo", "city": "bar"},
                private=True
            )
        )

        response = self.fetch(
            "/lab/foo", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.save")
    @mock.patch("utils.db.find_one")
    def test_post_correct_with_id_lab_id_found_err_on_save(
            self, find_one, save, mock_id):
        mock_id.return_value = "foo"
        lab_json = {
            "name": "foo",
            "token": "token-id",
            "contact": {
                "name": "foo",
                "surname": "bar",
                "email": "foo"
            },
            "address": {
                "street_1": "foo"
            }
        }
        find_one.side_effect = [lab_json]
        save.side_effect = [(500, None)]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foo"},
                address={"street_1": "foo"}
            )
        )

        response = self.fetch(
            "/lab/foo", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 500)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_post_correct_with_id_lab_id_found_and_token(
            self, find_one, mock_id):
        old_lab_json = {
            "name": "foo",
            "token": "token-id",
            "contact": {
                "name": "foo",
                "surname": "bar",
                "email": "foo"
            },
            "address": {
                "street_1": "foo"
            }
        }
        old_token_json = {
            "_id": "old-token-id",
            "token": "token-id",
            "email": ""
        }

        new_token_json = {
            "_id": "new-token-id",
            "token": "token-uuid",
            "email": "foo",
            "username": "bar"
        }

        mock_id.return_value = "foo"
        find_one.side_effect = [old_lab_json, old_token_json, new_token_json]

        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(
            dict(
                name="foo",
                contact={"name": "bar", "surname": "foo", "email": "foobar"},
                token="token-uuid"
            )
        )

        response = self.fetch(
            "/lab/foo", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_get_by_id_not_found(self, find_one, mock_id):
        mock_id.return_value = "lab-01"
        find_one.side_effect = [None]

        headers = {"Authorization": "foo"}
        response = self.fetch("/lab/lab-01", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

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
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    def test_delete_no_token(self):
        self.find_token.return_value = None

        response = self.fetch("/lab/lab", method="DELETE")
        self.assertEqual(response.code, 403)

    @mock.patch("bson.objectid.ObjectId")
    def test_delete_with_token_no_lab(self, mock_id):
        mock_id.return_value = "foolab"
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/foolab", method="DELETE", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("bson.objectid.ObjectId")
    def test_delete_with_token_with_lab(self, mock_id):
        mock_id.return_value = "lab"
        db = self.mongodb_client["kernel-ci"]
        db["lab"].insert(
            dict(_id="lab", name="lab-01", contact={}, address={}))

        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/lab/lab", method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_id_no_spec(self):
        headers = {"Authorization": "foo"}

        response = self.fetch("/lab", method="DELETE", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
