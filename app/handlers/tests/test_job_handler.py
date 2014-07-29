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

"""Test module for the JobHandler handler."""

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
from urls import _JOB_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestJobHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestJobHandler, self).setUp()

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
        }

        return web.Application([_JOB_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    @patch('utils.db.find')
    @patch('utils.db.count')
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = '{"count": 0, "code": 200, "limit": 0, "result": "[]"}'

        headers = {'X-Linaro-Token': 'foo'}
        response = self.fetch('/api/job', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    @patch('utils.db.find')
    @patch('utils.db.count')
    def test_get_with_limit(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = (
            '{"count": 0, "code": 200, "limit": 1024, "result": "[]"}'
        )

        headers = {'X-Linaro-Token': 'foo'}
        response = self.fetch('/api/job?limit=1024', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    @patch('handlers.job.JobHandler.collection')
    def test_get_by_id_not_found(self, collection):
        collection.find_one = MagicMock()
        collection.find_one.return_value = None

        headers = {'X-Linaro-Token': 'foo'}
        response = self.fetch('/api/job/job-kernel', headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.job.JobHandler.collection')
    def test_get_by_id_found(self, collection):
        collection.find_one = MagicMock()
        collection.find_one.return_value = []

        expected_body = '{"code": 200, "result": "[]"}'

        headers = {'X-Linaro-Token': 'foo'}
        response = self.fetch('/api/job/job-kernel', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, expected_body)

    def test_post_without_token(self):

        body = json.dumps(dict(job='job', kernel='kernel'))

        response = self.fetch('/api/job', method='POST', body=body)

        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_not_json_content(self):
        headers = {'X-Linaro-Token': 'foo', 'Content-Type': 'application/json'}

        response = self.fetch(
            '/api/job', method='POST', body='', headers=headers
        )

        self.assertEqual(response.code, 420)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_content_type(self):
        headers = {'X-Linaro-Token': 'foo'}

        response = self.fetch(
            '/api/job/job', method='POST', body='', headers=headers
        )

        self.assertEqual(response.code, 415)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post_wrong_json(self):
        headers = {'X-Linaro-Token': 'foo', 'Content-Type': 'application/json'}

        body = json.dumps(dict(foo='foo', bar='bar'))

        response = self.fetch(
            '/api/job/job', method='POST', body=body, headers=headers
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @patch('handlers.job.send_emails')
    @patch('handlers.job.import_job')
    def test_post_correct(self, mock_import_job, mock_send_emails):
        mock_import_job.apply_async = MagicMock()

        headers = {
            'X-Linaro-Token': 'foo',
            'Content-Type': 'application/json',
        }

        body = json.dumps(dict(job='job', kernel='kernel'))

        response = self.fetch(
            '/api/job', method='POST', headers=headers, body=body
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch('/api/job/job', method='DELETE')
        self.assertEqual(response.code, 403)

    def test_delete_with_token_no_job(self):
        headers = {'X-Linaro-Token': 'foo'}

        response = self.fetch(
            '/api/job/job', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_with_token_with_job(self):
        db = self.mongodb_client['kernel-ci']
        db['job'].insert(dict(_id='job', job='job', kernel='kernel'))

        headers = {'X-Linaro-Token': 'foo'}

        response = self.fetch(
            '/api/job/job', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
