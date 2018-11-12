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

"""Test module for the BuildHandler handler."""

try:
    import simplejson as json
except ImportError:
    import json

import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestBuildHandler(TestHandlerBase):

    def get_app(self):
        app_urls = [
            urls._BUILD_ID_URL,
            urls._BUILD_URL
        ]
        return tornado.web.Application(app_urls, **self.settings)

    def test_get_wrong_url(self):
        response = self.fetch("/foobarbuild")

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.find")
    @mock.patch("utils.db.count")
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = {
            "count": 0,
            "code": 200,
            "limit": 0,
            "skip": 0,
            "result": []
        }

        headers = {"Authorization": "foo"}
        response = self.fetch("/build", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        self.assertDictEqual(json.loads(response.body), expected_body)

    def test_get_old_defconfig_url(self):
        headers = {"Authorization": "foo"}
        response = self.fetch("/defconfig", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one2")
    def test_get_by_id_not_found(self, mock_find, mock_id):
        mock_id.return_value = "build"
        mock_find.return_value = None

        headers = {"Authorization": "foo"}
        response = self.fetch("/build/" + self.doc_id, headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_no_token(self):
        response = self.fetch("/build", method="POST", body="")

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_not_json_content(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}

        response = self.fetch(
            "/build", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 422)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_content_type(self):
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/build", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_wrong_json(self):
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(dict(foo="foo", bar="bar"))

        response = self.fetch(
            "/build", method="POST", body=body, headers=headers)

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.build.import_build")
    def test_post_correct(self, mock_import):
        mock_import.apply_async = mock.MagicMock()
        headers = {"Authorization": "foo", "Content-Type": "application/json"}
        body = json.dumps(
            dict(
                job="job",
                kernel="kernel",
                defconfig="defconfig",
                arch="arch",
                git_branch="branch",
                build_environment="build_environment"
            )
        )

        response = self.fetch(
            "/build", method="POST", headers=headers, body=body)

        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete(self):
        self.database["build"].insert(dict(_id=self.doc_id, job_id="job"))

        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/build/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("utils.db.delete")
    def test_delete_not_found(self, mock_delete):
        mock_delete.return_value = 404
        headers = {"Authorization": "foo"}

        response = self.fetch(
            "/build/" + self.doc_id, method="DELETE", headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
