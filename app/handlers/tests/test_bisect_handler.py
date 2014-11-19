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

"""Test module for the BisectHandler handler."""

import concurrent.futures
import mock
import mongomock
import tornado
import tornado.testing

import handlers.app
import urls

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = 'application/json; charset=UTF-8'


class TestBisectHandler(
        tornado.testing.AsyncHTTPTestCase, tornado.testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()
        super(TestBisectHandler, self).setUp()

        self.task_return_value = mock.MagicMock()
        self.task_ready = mock.MagicMock()
        self.task_ready.return_value = True
        self.task_return_value.ready = self.task_ready
        self.task_return_value.get = mock.MagicMock()
        self.task_return_value.get.return_value = 200, []

        patched_boot_bisect_func = mock.patch("taskqueue.tasks.boot_bisect")
        self.boot_bisect = patched_boot_bisect_func.start()
        self.boot_bisect.apply_async = mock.MagicMock()
        self.boot_bisect.apply_async.return_value = self.task_return_value

        patched_find_token = mock.patch("handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = True

        self.addCleanup(patched_find_token.stop)
        self.addCleanup(patched_validate_token.stop)
        self.addCleanup(patched_boot_bisect_func.stop)

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

        return tornado.web.Application([urls._BISECT_URL], **settings)

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_bisect_wrong_collection(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch('/bisect/foo/doc_id', headers=headers)
        self.assertEqual(response.code, 400)

    def test_boot_bisect_no_token(self):
        self.find_token.return_value = None

        response = self.fetch('/bisect/boot/id')
        self.assertEqual(response.code, 403)

    def test_boot_bisect_wrong_url(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch('/bisect/boot/', headers=headers)
        self.assertEqual(response.code, 400)

    @mock.patch("bson.objectid.ObjectId")
    def test_boot_bisect_no_id(self, mock_id):
        mock_id.return_value = "foo"
        headers = {'Authorization': 'foo'}

        self.task_return_value.get.return_value = 404, []

        response = self.fetch('/bisect/boot/foo', headers=headers)
        self.assertEqual(response.code, 404)

    def test_boot_bisect_no_faile(self):
        headers = {'Authorization': 'foo'}

        self.task_return_value.get.return_value = 400, None

        response = self.fetch('/bisect/boot/foo', headers=headers)
        self.assertEqual(response.code, 400)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.find_one")
    def test_boot_bisect_with_result(self, mocked_find, mock_id):
        mock_id.return_value = "foo"
        headers = {'Authorization': 'foo'}

        mocked_find.return_value = [{"foo": "bar"}]

        response = self.fetch('/bisect/boot/foo', headers=headers)
        self.assertEqual(response.code, 200)
