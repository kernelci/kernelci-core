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

import datetime
import json
import netaddr
import random
import types
import unittest
import uuid

from bson import (
    json_util,
    tz_util,
)

import models.base as modb
import models.token as modt


class TestTokenModel(unittest.TestCase):

    def test_token_model_is_base_document(self):
        token_obj = modt.Token()
        self.assertIsInstance(token_obj, modb.BaseDocument)

    def test_properties_len(self):
        token_obj = modt.Token()
        self.assertEqual(len(token_obj.properties), 16)

    def test_not_expired(self):
        token_obj = modt.Token()
        self.assertFalse(token_obj.expired)

    def test_token_not_none(self):
        token_obj = modt.Token()
        self.assertIsNotNone(token_obj.token)

    def test_unique_token(self):
        token_obj1 = modt.Token()
        token_obj2 = modt.Token()

        self.assertNotEqual(token_obj1.token, token_obj2.token)

    def test_token_creation_date(self):
        token_obj = modt.Token()
        self.assertIsInstance(token_obj.created_on, datetime.datetime)

    def test_token_to_dict_is_dict(self):
        token_obj = modt.Token()
        token_obj.id = "token-id"
        token_obj.email = "foo@example.org"
        token_obj.created_on = "now"
        token_obj.token = "token"
        token_obj.username = "user"

        expected = {
            "_id": "token-id",
            "created_on": "now",
            "email": "foo@example.org",
            "expired": False,
            "expires_on": None,
            "ip_address": None,
            "name": "foo@example.org",
            "properties": [0 for _ in range(0, 16)],
            "token": "token",
            "username": "user",
        }

        obtained = token_obj.to_dict()

        self.assertIsInstance(obtained, types.DictionaryType)
        self.assertDictEqual(expected, obtained)

    def test_token_is_admin(self):
        token_obj = modt.Token()
        token_obj.is_admin = 1

        self.assertEqual(token_obj.is_admin, 1)
        self.assertEqual(token_obj.can_create_token, 1)
        self.assertEqual(token_obj.is_superuser, 1)
        self.assertEqual(token_obj.is_get_token, 1)
        self.assertEqual(token_obj.is_delete_token, 1)
        self.assertEqual(token_obj.is_post_token, 1)

    def test_token_is_superuser(self):
        token_obj = modt.Token()
        token_obj.is_superuser = 1

        self.assertEqual(token_obj.is_admin, 0)
        self.assertEqual(token_obj.can_create_token, 0)
        self.assertEqual(token_obj.is_superuser, 1)
        self.assertEqual(token_obj.is_get_token, 1)
        self.assertEqual(token_obj.is_delete_token, 1)
        self.assertEqual(token_obj.is_post_token, 1)

    def test_token_wrong_numeric_value(self):
        token_obj = modt.Token()
        self.assertRaises(ValueError, setattr, token_obj, "is_admin", 2)

    def test_token_wrong_type(self):
        token_obj = modt.Token()
        self.assertRaises(TypeError, setattr, token_obj, "is_admin", "1")

    def test_token_negative_number(self):
        token_obj = modt.Token()
        self.assertRaises(ValueError, setattr, token_obj, "is_admin", -22)

    def test_token_properties_setter_wrong_type(self):
        token_obj = modt.Token()

        self.assertRaises(TypeError, setattr, token_obj, "properties", "")
        self.assertRaises(TypeError, setattr, token_obj, "properties", ())
        self.assertRaises(TypeError, setattr, token_obj, "properties", {})

    def test_token_properties_setter_wrong_len(self):
        token_obj = modt.Token()
        expected = [0 for _ in range(0, 16)]

        # Make sure the list we have is all 0 and 16 in length.
        self.assertListEqual(token_obj.properties, expected)
        self.assertRaises(
            ValueError, setattr, token_obj,
            "properties", [0 for _ in range(0, random.randint(0, 15))]
        )
        self.assertRaises(
            ValueError, setattr, token_obj,
            "properties", [0 for _ in range(0, random.randint(17, 1024))]
        )
        self.assertRaises(ValueError, setattr, token_obj, "properties", [])

    def test_token_valid_negative_number(self):
        token_obj = modt.Token()
        token_obj.is_superuser = -1

        self.assertTrue(token_obj.is_superuser)

    def test_token_with_boolean(self):
        token_obj = modt.Token()
        token_obj.is_admin = True

        self.assertTrue(token_obj.is_admin)
        self.assertEqual(token_obj.is_admin, 1)

    def test_token_wrong_expiry(self):
        token_obj = modt.Token()
        self.assertRaises(
            ValueError, setattr, token_obj, "expires_on", "2014-06"
        )

    def test_token_expiry_correct_single_digit(self):
        expire_str = "2014-7-1"

        token_obj = modt.Token()
        token_obj.expires_on = expire_str

        expected = datetime.datetime(2014, 7, 1, 0, 0)

        self.assertEqual(expected, token_obj.expires_on)

    def test_token_expiry_correct_double_digits(self):
        expire_str = "2014-07-01"

        token_obj = modt.Token()
        token_obj.expires_on = expire_str

        expected = datetime.datetime(2014, 7, 1, 0, 0)

        self.assertEqual(expected, token_obj.expires_on)

    def test_token_from_json(self):
        token_string = str(uuid.uuid4())
        now = datetime.datetime.now(tz=tz_util.utc)

        token_dict = {
            "username": "foo",
            "token": token_string,
            "created_on": now,
            "ip_address": None,
            "expired": True,
            "email": "bar@foo",
            "expires_on": None,
            "properties": [1 for _ in range(0, 16)],
            "name": "bar@foo",
            "_id": "token-id",
        }

        token = modt.Token.from_json(
            json.dumps(token_dict, default=json_util.default)
        )

        self.assertIsInstance(token, modt.Token)
        self.assertEqual(token.properties, [1 for _ in range(0, 16)])
        self.assertEqual(token.token, token_string)
        self.assertEqual(token.email, "bar@foo")
        self.assertEqual(token.name, "bar@foo")
        self.assertEqual(token.id, "token-id")
        self.assertTrue(token.expired)

    def test_ip_address_check_type_error(self):
        self.assertRaises(TypeError, modt.check_ip_address, 'foo')

    def test_ip_address_check_value_error(self):
        addrlist = ['foo']
        self.assertRaises(ValueError, modt.check_ip_address, addrlist)

    def test_ip_address_check_with_ip_address(self):
        addrlist = ['127.0.0.1']
        token_obj = modt.Token()
        token_obj.ip_address = addrlist

        expected = [netaddr.IPAddress('127.0.0.1').ipv6(ipv4_compatible=True)]
        self.assertEqual(expected, token_obj.ip_address)

    def test_ip_address_check_with_ip_network(self):
        addrlist = ['192.0.4.0/25']
        token_obj = modt.Token()
        token_obj.ip_address = addrlist

        expected = [
            netaddr.IPNetwork('192.0.4.0/25').ipv6(ipv4_compatible=True)
        ]
        self.assertEqual(expected, token_obj.ip_address)

    def test_ip_address_check_with_ip_network_and_address(self):
        addrlist = ['192.0.4.0/25', '127.0.0.1']
        token_obj = modt.Token()
        token_obj.ip_address = addrlist

        expected = [
            netaddr.IPNetwork('192.0.4.0/25').ipv6(ipv4_compatible=True),
            netaddr.IPAddress('127.0.0.1').ipv6(ipv4_compatible=True)
        ]
        self.assertEqual(expected, token_obj.ip_address)

    def test_valid_ip_no_restricted(self):
        token_obj = modt.Token()
        self.assertTrue(token_obj.is_valid_ip("foo"))

    def test_valid_ip_single_ip(self):
        token_obj = modt.Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '127.0.0.1'

        self.assertTrue(token_obj.is_valid_ip('127.0.0.1'))
        self.assertFalse(token_obj.is_valid_ip('127.0.0.3'))

    def test_valid_ip_single_ip_wrong_address(self):
        token_obj = modt.Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '127.0.0.1'

        self.assertFalse(token_obj.is_valid_ip("a.b.c"))

    def test_valid_ip_network(self):
        token_obj = modt.Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = '192.0.4.0/25'

        self.assertTrue(token_obj.is_valid_ip('192.0.4.125'))
        self.assertFalse(token_obj.is_valid_ip('192.0.5.1'))

    def test_valid_ip_mix_valid(self):
        token_obj = modt.Token()
        token_obj.is_ip_restricted = True
        token_obj.ip_address = ['10.2.3.4', '192.0.4.0/25']

        self.assertTrue(token_obj.is_valid_ip('192.0.4.1'))
        self.assertTrue(token_obj.is_valid_ip('10.2.3.4'))
        self.assertFalse(token_obj.is_valid_ip('192.1.4.0'))
        self.assertFalse(token_obj.is_valid_ip('10.2.3.3'))
        self.assertFalse(token_obj.is_valid_ip('127.0.0.1'))
