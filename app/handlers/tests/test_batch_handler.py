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

"""Test module for the BatchHandler handler."""

import json
import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestBatchHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._BATCH_URL], **self.settings)

    def test_delete_no_token(self):
        response = self.fetch("/batch", method="DELETE")
        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_with_token(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/batch", method="DELETE", headers=headers,
        )

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_get_no_token(self):
        response = self.fetch("/batch", method="GET")
        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_get_with_token(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/batch", method="GET", headers=headers,
        )

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_without_token(self):
        self.find_token.return_value = None

        batch_dict = {
            "batch": [
                {"method": "GET", "collection": "count", "operation_id": "foo"}
            ]
        }
        body = json.dumps(batch_dict)

        response = self.fetch("/batch", method="POST", body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/batch", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/batch", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/batch", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.common.run_batch_group")
    def test_post_correct(self, mocked_run_batch):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        batch_dict = {
            "batch": [
                {
                    "method": "GET",
                    "resource": "count",
                    "document": "boot",
                    "operation_id": "bar",
                    "query": "foo=bar"
                }
            ]
        }
        body = json.dumps(batch_dict)

        mocked_run_batch.return_value = {}

        response = self.fetch(
            "/batch", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mocked_run_batch.assert_called_once_with(
            [
                {
                    "resource": "count",
                    "method": "GET",
                    "document": "boot",
                    "operation_id": "bar",
                    "query": "foo=bar"
                }
            ],
            {
                "mongodb_user": "",
                "mongodb_password": ""
            }
        )
