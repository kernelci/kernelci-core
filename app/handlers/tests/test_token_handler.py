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

"""Test module for the TokenHandler handler."""

import json
import mongomock

from concurrent.futures import ThreadPoolExecutor
from mock import (
    MagicMock,
    patch,
)
from tornado import (
    ioloop,
    testing,
    web,
)

from handlers.app import AppHandler
from urls import _TOKEN_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestTokenHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestTokenHandler, self).setUp()

        patched_find_token = patch('handlers.decorators._find_token')
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = patch('handlers.decorators._validate_token')
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = True

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)

    def get_app(self):
        settings = {
            'client': self.mongodb_client,
            'executor': ThreadPoolExecutor(max_workers=2),
            'default_handler_class': AppHandler,
            'master_key': 'bar',
            'debug': False,
        }

        return web.Application([_TOKEN_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_get_no_token(self):
        response = self.fetch('/api/token')

        self.assertEqual(response.code, 403)

    @patch('utils.db.find')
    @patch('utils.db.count')
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = '{"count": 0, "code": 200, "limit": 0, "result": "[]"}'

        headers = {'X-Linaro-Token': 'foo'}
        response = self.fetch('/api/token', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    @patch('handlers.decorators._is_master_key')
    @patch('utils.db.find')
    @patch('utils.db.count')
    def test_get_token_is_master_key(
            self, mock_count, mock_find, mock_master_key):
        mock_count.return_value = 0
        mock_find.return_value = []
        mock_master_key.return_value = True

        self.find_token.return_value = 'bar'

        expected_body = '{"count": 0, "code": 200, "limit": 0, "result": "[]"}'

        headers = {'X-Linaro-Token': 'bar'}
        response = self.fetch('/api/token', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)
        self.assertTrue(mock_master_key.called)

    def test_post_without_token(self):
        body = json.dumps(dict(email='foo'))

        response = self.fetch('/api/token', method='POST', body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_content_type(self):
        headers = {'X-Linaro-Token': 'foo'}

        response = self.fetch(
            '/api/token', method='POST', body='', headers=headers
        )

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_not_json_content(self):
        headers = {'X-Linaro-Token': 'foo', 'Content-Type': 'application/json'}

        response = self.fetch(
            '/api/token', method='POST', body='', headers=headers
        )

        self.assertEqual(response.code, 420)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json(self):
        headers = {'X-Linaro-Token': 'foo', 'Content-Type': 'application/json'}

        body = json.dumps(dict(foo='foo', bar='bar'))

        response = self.fetch(
            '/api/token', method='POST', body=body, headers=headers
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_no_email(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(username='foo'))

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_wrong_value(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(email="bar", username='foo', get="1"))

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_ip_restricted_wrong_0(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(email="bar", username='foo', ip_restricted=1))

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_ip_restricted_wrong_1(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(email="bar", username='foo', ip_address="127"))

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_ip_restricted_wrong_2(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(
            dict(email="bar", username='foo', ip_restricted=0, ip_address="127")
        )

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_expires_wrong(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(
            dict(email="bar", expires_on="2014")
        )

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_new_correct(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(
            dict(
                email="bar", username='foo', expires_on="2014-07-01",
                admin=1, superuser=1, get=1, delete=1, post=1
            )
        )

        response = self.fetch(
            '/api/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertIsNotNone(response.headers['Location'])

    def test_post_update_no_token(self):
        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(admin=1))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.token.TokenHandler.collection')
    def test_post_update_with_token(self, mock_collection):

        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = dict(token='token')

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(admin=1))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.token.TokenHandler.collection')
    def test_post_update_wrong_content_0(self, mock_collection):

        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = dict(token='token')

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(admin="bar"))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.token.TokenHandler.collection')
    def test_post_update_wrong_content_1(self, mock_collection):

        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = dict(
            token='token', email='email', properties=[0 for _ in range(0, 16)]
        )

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(ip_address="127"))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.token.TokenHandler.collection')
    def test_post_update_wrong_content_2(self, mock_collection):

        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = dict(
            token='token', email='email', properties=[0 for _ in range(0, 16)]
        )

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(ip_restricted=1))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.token.TokenHandler.collection')
    def test_post_update_ip_restricted(self, mock_collection):

        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = dict(
            token='token', email='email', properties=[0 for _ in range(0, 16)]
        )

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(email="foo", ip_restricted=1, ip_address="127"))

        response = self.fetch(
            '/api/token/token', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
