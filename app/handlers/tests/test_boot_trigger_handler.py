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

"""Test module for BootTriggerHandler."""

import mock
import tornado

import handlers.boot_trigger as hbtrigger
import handlers.response as hresponse
import models.token as mtoken
import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestBootTriggerHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application(
            [urls._BOOT_TRIGGER_URL], **self.settings)

    def test_delete_not_implemented(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/trigger/boot", headers=headers, method="DELETE")

        self.assertEqual(response.code, 501)

    def test_put_not_implemented(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/trigger/boot", body="", headers=headers, method="PUT")

        self.assertEqual(response.code, 501)

    def test_post_not_implemented(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/trigger/boot", body="", headers=headers, method="POST")

        self.assertEqual(response.code, 501)

    def test_get_no_token(self):
        self.find_token.return_value = None

        response = self.fetch("/trigger/boot", method="GET")
        self.assertEqual(response.code, 403)

    @mock.patch("handlers.boot_trigger._is_lab_token")
    def test_get_no_lab_token(self, mock_is_lab):
        mock_is_lab.return_value = (False, False, None)

        headers = {"Authorization": "foo"}
        response = self.fetch("/trigger/boot", headers=headers, method="GET")

        self.assertEqual(response.code, 403)

    @mock.patch("handlers.boot_trigger.BootTriggerHandler._get",)
    @mock.patch("handlers.boot_trigger._is_lab_token")
    def test_get_with_lab_token(self, mock_is_lab, mock_get):
        mock_is_lab.return_value = (True, False, "lab")
        mock_get.return_value = hresponse.HandlerResponse()

        headers = {"Authorization": "foo"}
        response = self.fetch("/trigger/boot", headers=headers, method="GET")

        self.assertEqual(response.code, 200)

    @mock.patch("handlers.boot_trigger.BootTriggerHandler._get",)
    @mock.patch("handlers.boot_trigger._is_lab_token")
    def test_get_with_admin_token(self, mock_is_lab, mock_get):
        mock_is_lab.return_value = (False, True, None)
        mock_get.return_value = hresponse.HandlerResponse()

        headers = {"Authorization": "foo"}
        response = self.fetch("/trigger/boot", headers=headers, method="GET")

        self.assertEqual(response.code, 200)

    @mock.patch("handlers.boot_trigger._is_lab_token")
    def test_get_with_lab_token_no_lab(self, mock_is_lab):
        mock_is_lab.return_value = (True, False, None)

        headers = {"Authorization": "foo"}
        response = self.fetch("/trigger/boot", headers=headers, method="GET")

        self.assertEqual(response.code, 400)

    @mock.patch("utils.db.find_one2",)
    def test_get_lab_name_none(self, mock_find):
        mock_find.return_value = {}
        token = mtoken.Token()

        lab_name = hbtrigger._get_lab_name(token, self.database)

        self.assertIsNone(lab_name)

    @mock.patch("utils.db.find_one2",)
    def test_get_lab_name_with_name(self, mock_find):
        mock_find.return_value = {"name": "fake_name"}
        token = mtoken.Token()

        lab_name = hbtrigger._get_lab_name(token, self.database)

        self.assertIsNotNone(lab_name)
        self.assertEqual("fake_name", lab_name)

    def test_is_lab_token_admin_super(self):
        token = mtoken.Token()
        token.is_admin = True

        is_lab, is_super, lab_name = hbtrigger._is_lab_token(
            token, self.database)

        self.assertTrue(is_lab)
        self.assertTrue(is_super)
        self.assertIsNone(lab_name)

        token.is_admin = False
        token.is_superuser = True

        is_lab, is_super, lab_name = hbtrigger._is_lab_token(
            token, self.database)

        self.assertTrue(is_lab)
        self.assertTrue(is_super)
        self.assertIsNone(lab_name)

    @mock.patch("handlers.boot_trigger._get_lab_name")
    def test_is_lab_token_normal(self, mock_get_lab):
        token = mtoken.Token()
        token.is_lab_token = True
        mock_get_lab.return_value = "fake"

        is_lab, is_super, lab_name = hbtrigger._is_lab_token(
            token, self.database)

        self.assertTrue(is_lab)
        self.assertFalse(is_super)
        self.assertIsNotNone(lab_name)

        token.is_lab_token = False

        is_lab, is_super, lab_name = hbtrigger._is_lab_token(
            token, self.database)

        self.assertFalse(is_lab)
        self.assertFalse(is_super)
        self.assertIsNone(lab_name)
