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

import tornado

try:
    import simplejson as json
except ImportError:
    import json

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestCallbackHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application(
            [urls._LAVA_CALLBACK_URL], **self.settings)

    def test_get_wrong_url(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/callback", method="GET", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_get(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/callback/lava/boot", method="GET", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/callback/lava/boot", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_no_token(self):
        response = self.fetch("/callback/lava/boot", method="POST", body="")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_token_wrong_content(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.fetch(
            "/callback/lava/boot", method="POST", body="", headers=headers)
        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_token_missing_content(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json"
        }
        response = self.fetch(
            "/callback/lava/boot", method="POST", body="", headers=headers)
        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_token_missing_query_parameter(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json"
        }
        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/callback/lava/boot", method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_action(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json"
        }
        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/callback/lava/foo", method="POST", body=body, headers=headers)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
