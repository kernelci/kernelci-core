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

"""Test module for the JobLogsHandler."""

try:
    import simplejson as json
except ImportError:
    import json

import bson

import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestJobLogsHandler(TestHandlerBase):

    def setUp(self):
        super(TestJobLogsHandler, self).setUp()
        self.url_id = "/job/" + self.doc_id + "/logs/"
        self.url = "/job/logs"

    def get_app(self):
        return tornado.web.Application(
            [urls._JOB_ID_LOGS_URL, urls._JOB_LOGS_URL], **self.settings)

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
            response.headers["Content-Type"], self.content_type)

    @mock.patch("handlers.base.BaseHandler.validate_req_token")
    def test_get_invalid_token(self, mock_validate):
        mock_validate.return_value = (False, None)
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_one2")
    def test_get_not_found(self, mock_find):
        mock_find.return_value = None
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    def test_get_wrong_id(self, mock_id):
        mock_id.side_effect = bson.errors.InvalidId("Wrong")
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_one2")
    def test_get_valid(self, mock_find):
        mock_find.return_value = {"_id": self.doc_id}
        headers = {"Authorization": "bar"}
        response = self.fetch(self.url_id, method="GET", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find_and_count")
    def test_get_valid_no_id(self, mock_find):
        mock_find.return_value = ({"_id": self.doc_id}, 1)
        headers = {"Authorization": "bar"}
        response = self.fetch(
            self.url + "?job=foo", method="GET", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
