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

try:
    import simplejson as json
except ImportError:
    import json

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

        patched_find_token = mock.patch(
            "handlers.base.BaseHandler._find_token")
        self.find_token = patched_find_token.start()
        self.find_token.return_value = "token"

        patched_validate_token = mock.patch("handlers.common.validate_token")
        self.validate_token = patched_validate_token.start()
        self.validate_token.return_value = (True, "token")

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

    @mock.patch("bson.objectid.ObjectId")
    def test_delete_with_token_no_job(self, mock_id):
        mock_id.return_value = "boot"
        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @mock.patch("handlers.boot.BootHandler._valid_boot_delete_token")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_with_token_with_boot(self, mock_id, valid_delete):
        valid_delete.return_value = True
        mock_id.return_value = "boot"
        db = self.mongodb_client['kernel-ci']
        db['boot'].insert(dict(_id='boot', job='job', kernel='kernel'))

        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.headers['Content-Type'], DEFAULT_CONTENT_TYPE)

    @mock.patch("handlers.boot.BootHandler._valid_boot_delete_token")
    @mock.patch("bson.objectid.ObjectId")
    def test_delete_with_non_lab_token_with_boot(self, mock_id, valid_delete):
        valid_delete.return_value = False
        mock_id.return_value = "boot"
        db = self.mongodb_client['kernel-ci']
        db['boot'].insert(dict(_id='boot', job='job', kernel='kernel'))

        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/boot', method='DELETE', headers=headers,
        )

        self.assertEqual(response.code, 403)
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

    def test_delete_with_bogus_objectid(self):
        headers = {'Authorization': 'foo'}

        response = self.fetch(
            '/boot/!@#$!#$foo', method='DELETE', headers=headers,
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

    def test_post_wrong_content(self):
        body = {
            "foo": "bar"
        }

        headers = {
            'Authorization': 'foo',
            'Content-Type': 'application/json',
        }

        response = self.fetch(
            "/boot", method="POST", body=json.dumps(body), headers=headers
        )

        self.assertEqual(response.code, 400)

    @mock.patch("taskqueue.tasks.import_boot")
    @mock.patch("utils.db.find_one")
    def test_post_valid_content_same_token(self, find_one, import_boot):
        find_one.side_effect = [
            {"token": "foo"}, {"token": "foo", "expired": False}
        ]
        body = {
            "version": "1.0",
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "lab_name": "lab-name",
            "arch": "arm"
        }

        headers = {
            'Authorization': 'foo',
            'Content-Type': 'application/json',
        }

        response = self.fetch(
            "/boot", method="POST", body=json.dumps(body), headers=headers
        )

        self.assertEqual(response.code, 202)

    @mock.patch("utils.db.find_one")
    def test_post_valid_content_different_token(self, find_one):
        find_one.side_effect = [
            {"token": "bar"}, {"token": "bar", "expired": False}
        ]
        body = {
            "version": "1.0",
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "lab_name": "lab-name",
            "arch": "arm"
        }

        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }

        response = self.fetch(
            "/boot", method="POST", body=json.dumps(body), headers=headers
        )

        self.assertEqual(response.code, 403)

    @mock.patch("taskqueue.tasks.import_boot")
    @mock.patch("utils.db.find_one")
    def test_post_valid_content_different_token_admin(
            self, find_one, import_boot):
        token_prop = [0 for _ in range(0, 16)]
        token_prop[0] = [1]

        find_one.side_effect = [
            {"token": "bar"},
            {"token": "bar", "expired": False, "properties": token_prop}
        ]
        body = {
            "version": "1.0",
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "lab_name": "lab-name",
            "arch": "arm"
        }

        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }

        response = self.fetch(
            "/boot", method="POST", body=json.dumps(body), headers=headers
        )

        self.assertEqual(response.code, 202)
