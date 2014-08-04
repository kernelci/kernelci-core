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

import json
import unittest

from bson import (
    json_util,
    tz_util,
)
from datetime import datetime
from netaddr import (
    IPAddress,
    IPNetwork,
)
from uuid import uuid4
from types import DictionaryType

from models.base import BaseDocument
from models.token import Token


class TestTokenModel(unittest.TestCase):

    def test_token_model_is_base_document(self):
        token_obj = Token()
        self.assertIsInstance(token_obj, BaseDocument)

    def test_properties_len(self):
        token_obj = Token()
        self.assertEqual(len(token_obj.properties), 16)

    def test_not_expired(self):
        token_obj = Token()
        self.assertFalse(token_obj.expired)

    def test_token_not_none(self):
        token_obj = Token()
        self.assertIsNotNone(token_obj.token)

    def test_unique_token(self):
        token_obj1 = Token()
        token_obj2 = Token()

        self.assertNotEqual(token_obj1.token, token_obj2.token)

    def test_token_creation_date(self):
        token_obj = Token()
        self.assertIsInstance(token_obj.created_on, datetime)

    def test_token_to_dict_is_dict(self):
        token_obj = Token()

        self.assertIsInstance(token_obj.to_dict(), DictionaryType)

    def test_token_is_admin(self):
        token_obj = Token()
        token_obj.is_admin = 1

        self.assertEqual(token_obj.is_admin, 1)
        self.assertEqual(token_obj.can_create_token, 1)
        self.assertEqual(token_obj.is_superuser, 1)
        self.assertEqual(token_obj.is_get_token, 1)
        self.assertEqual(token_obj.is_delete_token, 1)
        self.assertEqual(token_obj.is_post_token, 1)

    def test_token_is_superuser(self):
        token_obj = Token()
        token_obj.is_superuser = 1

        self.assertEqual(token_obj.is_admin, 0)
        self.assertEqual(token_obj.can_create_token, 0)
        self.assertEqual(token_obj.is_superuser, 1)
        self.assertEqual(token_obj.is_get_token, 1)
        self.assertEqual(token_obj.is_delete_token, 1)
        self.assertEqual(token_obj.is_post_token, 1)

    def test_token_wrong_numeric_value(self):
        token_obj = Token()

        def _call_setter(value):
            token_obj.is_admin = value

        self.assertRaises(ValueError, _call_setter, 2)

    def test_token_wrong_type(self):
        token_obj = Token()

        def _call_setter(value):
            token_obj.is_admin = value

        self.assertRaises(TypeError, _call_setter, "1")

    def test_token_negative_number(self):
        token_obj = Token()

        def _call_setter(value):
            token_obj.is_admin = value

        self.assertRaises(ValueError, _call_setter, -22)

    def test_token_valid_negative_number(self):
        token_obj = Token()
        token_obj.is_superuser = -1

        self.assertTrue(token_obj.is_superuser)

    def test_token_with_boolean(self):
        token_obj = Token()
        token_obj.is_admin = True

        self.assertTrue(token_obj.is_admin)
        self.assertEqual(token_obj.is_admin, 1)

    def test_token_wrong_expiry(self):
        token_obj = Token()

        def _call_setter(value):
            token_obj.expires_on = value

        self.assertRaises(ValueError, _call_setter, "2014-06")

    def test_token_expiry_correct_single_digit(self):
        expire_str = "2014-7-1"

        token_obj = Token()
        token_obj.expires_on = expire_str

        expected = datetime(2014, 7, 1, 0, 0)

        self.assertEqual(expected, token_obj.expires_on)

    def test_token_expiry_correct_double_digits(self):
        expire_str = "2014-07-01"

        token_obj = Token()
        token_obj.expires_on = expire_str

        expected = datetime(2014, 7, 1, 0, 0)

        self.assertEqual(expected, token_obj.expires_on)

    def test_token_to_json(self):
        token_obj = Token()

        token_obj._created_on = '1'
        token_obj._token = '1'

        expected = (
            '{"username": null, "expired": false, "token": "1", '
            '"properties": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], '
            '"created_on": "1", "ip_address": null, "email": null, '
            '"expires_on": null}'
        )

        self.assertEqual(expected, token_obj.to_json())

    def test_token_to_json_with_ip(self):
        token_obj = Token()

        token_obj._created_on = '1'
        token_obj._token = '1'
        token_obj.ip_address = '127.0.0.1'
        token_obj.is_ip_restricted = True

        expected = (
            '{"username": null, "expired": false, "token": "1", '
            '"properties": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], '
            '"created_on": "1", "ip_address": ["::127.0.0.1"], '
            '"email": null, "expires_on": null}'
        )

        self.assertEqual(expected, token_obj.to_json())

    def test_token_from_json(self):
        token_string = str(uuid4())
        now = datetime.now(tz=tz_util.utc)

        token_dict = {
            "username": "foo",
            "token": token_string,
            "created_on": now,
            "ip_address": None,
            "expired": True,
            "email": "bar@foo",
            "expires_on": None,
            "properties": [1 for _ in range(0, 16)]
        }

        token = Token.from_json(
            json.dumps(token_dict, default=json_util.default)
        )

        self.assertIsInstance(token, Token)
        self.assertEqual(token.properties, [1 for _ in range(0, 16)])
        self.assertEqual(token.token, token_string)
        self.assertEqual(token.email, "bar@foo")
        self.assertTrue(token.expired)

    def test_ip_address_check_type_error(self):
        self.assertRaises(TypeError, Token.check_ip_address, 'foo')

    def test_ip_address_check_value_error(self):
        addrlist = ['foo']
        self.assertRaises(ValueError, Token.check_ip_address, addrlist)

    def test_ip_address_check_with_ip_address(self):
        addrlist = ['127.0.0.1']
        token_obj = Token()
        token_obj.ip_address = addrlist

        expected = [IPAddress('127.0.0.1').ipv6(ipv4_compatible=True)]
        self.assertEqual(expected, token_obj.ip_address)

    def test_ip_address_check_with_ip_network(self):
        addrlist = ['192.0.4.0/25']
        token_obj = Token()
        token_obj.ip_address = addrlist

        expected = [IPNetwork('192.0.4.0/25').ipv6(ipv4_compatible=True)]
        self.assertEqual(expected, token_obj.ip_address)

    def test_ip_address_check_with_ip_network_and_address(self):
        addrlist = ['192.0.4.0/25', '127.0.0.1']
        token_obj = Token()
        token_obj.ip_address = addrlist

        expected = [
            IPNetwork('192.0.4.0/25').ipv6(ipv4_compatible=True),
            IPAddress('127.0.0.1').ipv6(ipv4_compatible=True)
        ]
        self.assertEqual(expected, token_obj.ip_address)

    def test_valid_ip_no_restricted(self):
        token_obj = Token()
        self.assertTrue(token_obj.is_valid_ip("foo"))

    def test_valid_ip_single_ip(self):
        token_obj = Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '127.0.0.1'

        self.assertTrue(token_obj.is_valid_ip('127.0.0.1'))
        self.assertFalse(token_obj.is_valid_ip('127.0.0.3'))

    def test_valid_ip_single_ip_wrong_address(self):
        token_obj = Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '127.0.0.1'

        self.assertFalse(token_obj.is_valid_ip("a.b.c"))

    def test_valid_ip_network(self):
        token_obj = Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '192.0.4.0/25'

        self.assertTrue(token_obj.is_valid_ip('192.0.4.125'))
        self.assertFalse(token_obj.is_valid_ip('192.0.5.1'))

    def test_valid_ip_mix_valid(self):
        token_obj = Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = ['10.2.3.4', '192.0.4.0/25']

        self.assertTrue(token_obj.is_valid_ip('192.0.4.1'))
        self.assertTrue(token_obj.is_valid_ip('10.2.3.4'))
        self.assertFalse(token_obj.is_valid_ip('192.1.4.0'))
        self.assertFalse(token_obj.is_valid_ip('10.2.3.3'))
        self.assertFalse(token_obj.is_valid_ip('127.0.0.1'))
