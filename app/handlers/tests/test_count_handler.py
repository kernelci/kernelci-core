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

"""Test module for the CountHandler handler."""

import json
import mongomock

from concurrent.futures import ThreadPoolExecutor
from tornado import (
    ioloop,
    testing,
    web,
)

from handlers.app import AppHandler
from urls import _COUNT_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestCountHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestCountHandler, self).setUp()

    def get_app(self):
        settings = {
            'client': self.mongodb_client,
            'executor': ThreadPoolExecutor(max_workers=2),
            'default_handler_class': AppHandler,
        }

        return web.Application([_COUNT_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_post(self):
        body = json.dumps(dict(job='job', kernel='kernel'))

        response = self.fetch('/api/count', method='POST', body=body)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        response = self.fetch('/api/count', method='DELETE')

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_get_wrong_resource(self):
        response = self.fetch('/api/count/foobar', method='GET')

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_get_count_all(self):
        expected_body = (
            '{"code": 200, "result": "[{\\"count\\": 0, \\"collection\\": '
            '\\"job\\"}, {\\"count\\": 0, \\"collection\\": \\"boot\\"}, '
            '{\\"count\\": 0, \\"collection\\": \\"defconfig\\"}]"}'
        )

        response = self.fetch('/api/count', method='GET')

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    def test_get_count_collection(self):
        expected_body = (
            '{"code": 200, "result": "{\\"count\\": 0, '
            '\\"collection\\": \\"boot\\"}"}'
        )

        response = self.fetch('/api/count/boot', method='GET')

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    def test_get_count_collection_with_query(self):
        expected_body = (
            '{"code": 200, "result": "{\\"count\\": 0, \\"fields\\": '
            '{\\"board\\": \\"foo\\"}, \\"collection\\": \\"boot\\"}"}'
        )

        response = self.fetch('/api/count/boot?board=foo', method='GET')

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)
