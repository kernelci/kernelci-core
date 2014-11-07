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

"""Test module for the BootHandler handler."""

import concurrent.futures
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestBootHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestBootHandler, self).setUp()

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
            'debug': False
        }

        return tornado.web.Application([urls._BOOT_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_delete_no_token(self):
        self.find_token.return_value = None

        response = self.fetch('/boot/board', method='DELETE')
        self.assertEqual(response.code, 403)

    def test_delete_with_token_no_job(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_with_token_with_boot(self):
        db = self.mongodb_client['kernel-ci']
        db['boot'].insert(dict(_id='boot', job='job', kernel='kernel'))

        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_no_id_no_spec(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    def test_delete_wrong_spec(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot?status=FAIL&date_range=5&created_on=20140607&time=2',
            method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)
