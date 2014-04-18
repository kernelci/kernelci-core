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

"""Test module for the DefConfHandler handler.."""

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
from urls import _SUBSCRIPTION_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestSubscriptionHandler(
        testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestSubscriptionHandler, self).setUp()

    def get_app(self):
        settings = {
            'client': self.mongodb_client,
            'executor': ThreadPoolExecutor(max_workers=2),
            'default_handler_class': AppHandler,
        }

        return web.Application([_SUBSCRIPTION_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    @patch('utils.db.find')
    @patch('utils.db.count')
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = (
            '{"count": 0, "code": 200, "limit": 0, "result": "[]"}'
        )

        response = self.fetch('/api/subscription')

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    @patch('handlers.subscription.SubscriptionHandler.collection')
    def test_get_by_id_not_found(self, mock_collection):
        mock_collection.find_one = MagicMock()
        mock_collection.find_one.return_value = None

        response = self.fetch('/api/subscription/sub')

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_without_xsrf(self):

        body = json.dumps(dict(job='job', kernel='kernel'))

        response = self.fetch('/api/subscription', method='POST', body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_not_json(self):
        headers = {'X-XSRF-Header': 'foo'}

        response = self.fetch(
            '/api/subscription', method='POST', body='', headers=headers
        )

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('utils.subscription.find_one')
    def test_post_valid(self, mock_find_one):
        mock_find_one.return_value = dict(_id='sub', job_id='job', emails=[])

        headers = {'X-XSRF-Header': 'foo', 'Content-Type': 'application/json'}

        body = json.dumps(dict(job='job', email='email'))

        response = self.fetch(
            '/api/subscription', method='POST', body=body, headers=headers
        )

        self.assertEqual(response.code, 201)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('utils.subscription.find_one')
    def test_delete_valid_with_payload(self, mock_find_one):
        mock_find_one.return_value = dict(
            _id='sub', emails=['email'], job_id='job'
        )

        headers = {'X-XSRF-Header': 'foo', 'Content-Type': 'application/json'}

        body = json.dumps(dict(email='email'))

        response = self.fetch(
            '/api/subscription/sub', method='DELETE', body=body,
            headers=headers, allow_nonstandard_methods=True,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_valid_without_payload(self):
        headers = {'X-XSRF-Header': 'foo'}

        response = self.fetch(
            '/api/subscription/sub', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
