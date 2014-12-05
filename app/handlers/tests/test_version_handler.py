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

import concurrent.futures
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestVersionHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()

        super(TestVersionHandler, self).setUp()

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
            'version': 'foo'
        }

        return tornado.web.Application([urls._VERSION_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_get(self):
        response = self.fetch("/version", method="GET")
        self.assertEqual(response.code, 200,)

    def test_post(self):
        response = self.fetch("/version", method="POST", body="")
        self.assertEqual(response.code, 501)

    def test_delete(self):
        response = self.fetch("/version", method="DELETE")
        self.assertEqual(response.code, 501)
