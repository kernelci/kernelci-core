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

import concurrent.futures
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestDefconfHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestDefconfHandler, self).setUp()

        patched_find_token = mock.patch("handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = True

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)

    def get_app(self):
        dboptions = {
            'dbpassword': "",
            'dbuser': ""
        }

        settings = {
            'dboptions': dboptions,
            'client': self.mongodb_client,
            'executor': concurrent.futures.ThreadPoolExecutor(max_workers=2),
            'default_handler_class': handlers.app.AppHandler,
            'debug': False,
        }

        return tornado.web.Application([urls._DEFCONF_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_get_wrong_url(self):
        response = self.fetch('/foobardefconf')

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @mock.patch('utils.db.find')
    @mock.patch('utils.db.count')
    def test_get(self, mock_count, mock_find):
        mock_count.return_value = 0
        mock_find.return_value = []

        expected_body = (
            '{"count": 0, "code": 200, "limit": 0, "result": []}'
        )

        headers = {'Authorization': 'foo'}
        response = self.fetch('/defconfig', headers=headers)

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
        self.assertEqual(response.body, expected_body)

    @mock.patch('bson.objectid.ObjectId')
    @mock.patch('handlers.defconf.DefConfHandler.collection')
    def test_get_by_id_not_found(self, mock_collection, mock_id):
        mock_id.return_value = "defconf"
        mock_collection.find_one = mock.MagicMock()
        mock_collection.find_one.return_value = None

        headers = {'Authorization': 'foo'}
        response = self.fetch('/defconfig/defconf', headers=headers)

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_post(self):
        # POST is not implemented for the DefConfHandler.
        response = self.fetch('/defconfig', method='POST', body='')

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        db = self.mongodb_client['kernel-ci']
        db['defconfig'].insert(dict(_id='defconf', job_id='job'))

        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/defconfig/defconf', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
