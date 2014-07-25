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

import unittest

from datetime import date

from models.base import BaseDocument
from models.token import Token

from types import DictionaryType


class TestTokenModel(unittest.TestCase):

    def test_token_model_not_base_document(self):
        token_obj = Token()
        self.assertNotIsInstance(token_obj, BaseDocument)

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
        today = date.today()

        self.assertIsInstance(token_obj.created_on, date)
        self.assertEqual(today, token_obj.created_on)

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

    def test_token_with_boolean(self):
        token_obj = Token()
        token_obj.is_admin = True

        self.assertTrue(token_obj.is_admin)
        self.assertEqual(token_obj.is_admin, 1)
