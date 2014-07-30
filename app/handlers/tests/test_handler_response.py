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

"""Test class for HandlerResponse object."""

import unittest

from handlers.response import HandlerResponse


class TestHandlerResponse(unittest.TestCase):

    def test_response_constructor_not_valid_input(self):
        self.assertRaises(ValueError, HandlerResponse, "1")

    def test_response_setter_not_valid(self):
        response = HandlerResponse(1)

        def _setter_call(value):
            response.status_code = value

        self.assertRaises(ValueError, _setter_call, "1")

    def test_response_setter_valid(self):
        response = HandlerResponse(1)
        response.status_code = 200

        self.assertEqual(response.status_code, 200)

    def test_reponse_creation_default_values(self):
        response = HandlerResponse(0)

        self.assertEqual(response.headers, {})
        self.assertIsNone(response.message)

    def test_response_message_setter_not_valid(self):
        response = HandlerResponse(0)

        def _setter_call(value):
            response.message = value

        self.assertRaises(ValueError, _setter_call, 1)
        self.assertRaises(ValueError, _setter_call, True)
        self.assertRaises(ValueError, _setter_call, [])
        self.assertRaises(ValueError, _setter_call, {})

    def test_response_message_setter_valid(self):
        response = HandlerResponse(1)

        response.message = u'foo'
        self.assertEqual('foo', response.message)

        response.message = r'bar'
        self.assertEqual('bar', response.message)

    def test_response_headers_setter_not_valid(self):
        response = HandlerResponse(0)

        def _setter_call(value):
            response.headers = value

        self.assertRaises(ValueError, _setter_call, 1)
        self.assertRaises(ValueError, _setter_call, True)
        self.assertRaises(ValueError, _setter_call, [])
        self.assertRaises(ValueError, _setter_call, ())
        self.assertRaises(ValueError, _setter_call, "1")

    def test_response_headers_setter_valid(self):
        response = HandlerResponse(0)

        response.headers = {'foo': 'bar'}
        self.assertEqual({'foo': 'bar'}, response.headers)
