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

"""Test module for the ReportHandler."""

import mock
import tornado

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestReportHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._REPORT_URL], **self.settings)

    def test_post(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports", method="POST", body="", headers=headers)

        self.assertEqual(response.code, 501)

    def test_post_no_token(self):
        response = self.fetch("/reports", method="POST", body="")
        self.assertEqual(response.code, 403)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)

    def test_delete_no_token(self):
        response = self.fetch("/reports", method="DELETE")
        self.assertEqual(response.code, 403)

    def test_get_no_token(self):
        response = self.fetch("/reports")
        self.assertEqual(response.code, 403)

    @mock.patch("utils.db.find")
    @mock.patch("utils.db.count")
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch("/reports", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], self.content_type)

    @mock.patch("utils.db.find")
    @mock.patch("utils.db.count")
    def test_get_with_keys(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/reports?job=job&kernel=kernel", headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], self.content_type)
