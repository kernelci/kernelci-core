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

import datetime
import logging
import mock
import unittest

import handlers.common.token
import models.token as mtoken


class TestCommonToken(unittest.TestCase):

    def setUp(self):
        super(TestCommonToken, self).setUp()
        logging.disable(logging.CRITICAL)
        self.token = mtoken.Token()

    def tearDown(self):
        super(TestCommonToken, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_token_expires_expired(self):
        self.token.expires_on = "1970-01-01"

        self.assertIsInstance(self.token.expires_on, datetime.datetime)
        self.assertTrue(handlers.common.token.is_expired_token(self.token))

    def test_token_expires_not_expired(self):
        self.token.expires_on = "2300-01-01"

        self.assertIsInstance(self.token.expires_on, datetime.datetime)
        self.assertFalse(handlers.common.token.is_expired_token(self.token))

    def test_token_expires_is_expired(self):
        self.token.expired = True
        self.assertTrue(handlers.common.token.is_expired_token(self.token))

    def test_token_expires_is_not_expired(self):
        self.token.expired = False
        self.assertFalse(handlers.common.token.is_expired_token(self.token))

    def test_valid_token_tests(self):
        self.token.is_admin = True
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "DELETE"))

        self.token.is_admin = False
        self.token.is_superuser = True
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "DELETE"))

        self.token.is_superuser = False
        self.token.is_get_token = True
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "GET"))
        self.assertFalse(
            handlers.common.token.valid_token_tests(self.token, "POST"))
        self.assertFalse(
            handlers.common.token.valid_token_tests(self.token, "PUT"))
        self.assertFalse(
            handlers.common.token.valid_token_tests(self.token, "DELETE"))

        self.token.is_test_lab_token = True
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_tests(self.token, "DELETE"))

    def test_valid_token_general_true(self):
        self.token.is_get_token = True
        self.token.is_post_token = True
        self.token.is_delete_token = True
        self.token.is_lab_token = False

        self.assertFalse(self.token.is_lab_token)
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "DELETE"))
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "PUT"))

    def test_valid_token_general_lab_token(self):
        self.token.is_get_token = False
        self.token.is_post_token = True
        self.token.is_delete_token = True
        self.token.is_lab_token = True

        self.assertTrue(self.token.is_lab_token)
        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "POST"))
        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "DELETE"))
        self.assertTrue(
            handlers.common.token.valid_token_general(self.token, "PUT"))

    def test_valid_token_general_false(self):
        self.token.is_get_token = False
        self.token.is_post_token = False
        self.token.is_delete_token = False

        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "GET"))
        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "POST"))
        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "DELETE"))
        self.assertFalse(
            handlers.common.token.valid_token_general(self.token, "PUT"))

    def test_valid_token_bh(self):
        self.token.is_get_token = True
        self.token.is_post_token = True
        self.token.is_delete_token = True

        self.assertTrue(handlers.common.token.valid_token_bh(
            self.token, "GET"))
        self.assertTrue(handlers.common.token.valid_token_bh(
            self.token, "POST"))
        self.assertTrue(handlers.common.token.valid_token_bh(
            self.token, "DELETE"))

        self.token.is_get_token = False
        self.token.is_post_token = False
        self.token.is_delete_token = False

        self.assertFalse(handlers.common.token.valid_token_bh(
            self.token, "GET"))
        self.assertFalse(handlers.common.token.valid_token_bh(
            self.token, "POST"))
        self.assertFalse(handlers.common.token.valid_token_bh(
            self.token, "DELETE"))

    def test_valid_token_th_true(self):
        self.token.is_admin = True

        self.assertTrue(
            handlers.common.token.valid_token_th(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_th(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_th(self.token, "DELETE"))
        self.assertTrue(
            handlers.common.token.valid_token_th(self.token, "PUT}"))

        self.token.is_admin = False
        self.token.is_superuser = True

        self.assertTrue(
            handlers.common.token.valid_token_th(self.token, "GET"))

    def test_valid_token_th_false(self):
        self.token.is_admin = False
        self.token.is_superuser = False

        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "GET"))
        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "POST"))
        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "DELETE"))
        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "PUT"))

        self.token.is_admin = False
        self.token.is_superuser = True

        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "POST"))
        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "PUT"))
        self.assertFalse(
            handlers.common.token.valid_token_th(self.token, "DELETE"))

    def test_valid_token_upload_nornal_token(self):
        self.token.is_upload_token = True

        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "POST"))

        self.assertFalse(
            handlers.common.token.valid_token_upload(self.token, "GET"))
        self.assertFalse(
            handlers.common.token.valid_token_upload(self.token, "DELETE"))

    def test_valid_token_upload_admin(self):
        self.token.is_admin = True

        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "DELETE"))

    def test_valid_token_upload_superuser(self):
        self.token.is_superuser = True

        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "POST"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "PUT"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "GET"))
        self.assertTrue(
            handlers.common.token.valid_token_upload(self.token, "DELETE"))

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_wrong_class(self, mock_from_json):
        mock_from_json.return_value = mock.Mock()

        self.assertFalse(
            handlers.common.token.validate_token("foo", "GET", None, None)[0])
        self.assertFalse(
            handlers.common.token.validate_token(None, "GET", None, None)[0])

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_true(self, mock_from_json):
        token = mtoken.Token()

        mock_from_json.return_value = token
        validate_func = mock.Mock()
        validate_func.side_effect = [True, True]

        token.is_ip_restricted = False

        self.assertTrue(
            handlers.common.token.validate_token(
                token, "GET", None, validate_func)[0])

        token.is_ip_restricted = True
        token.ip_address = "127.0.0.1"

        self.assertTrue(
            handlers.common.token.validate_token(
                token, "GET", "127.0.0.1", validate_func)[0])

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_false(self, mock_from_json):
        token = mtoken.Token()

        mock_from_json.return_value = token
        validate_func = mock.Mock()
        validate_func.side_effect = [False, True, False]

        token.is_ip_restricted = True

        self.assertFalse(
            handlers.common.token.validate_token(
                token, "GET", None, validate_func)[0])

        token.is_ip_restricted = True
        token.ip_address = "127.1.1.1"

        self.assertFalse(
            handlers.common.token.validate_token(
                token, "GET", "127.0.0.1", validate_func)[0])

        token.is_ip_restricted = False

        self.assertFalse(
            handlers.common.token.validate_token(
                token, "GET", None, validate_func)[0])

    @mock.patch("models.token.Token.from_json")
    def test_validate_token_expired(self, mock_from_json):
        token = mtoken.Token()
        token.expired = True

        mock_from_json.return_value = token
        validate_func = mock.Mock()

        self.assertFalse(handlers.common.token.validate_token(
            token, "GET", None, validate_func)[0])
