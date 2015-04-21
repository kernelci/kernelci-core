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

"""Test module for the SendHandler."""

import datetime
import json
import mock
import mongomock

from concurrent.futures import ThreadPoolExecutor
from tornado import (
    ioloop,
    testing,
    web,
)

import handlers.send as sendh

from handlers.app import AppHandler
from urls import _SEND_URL

# Default Content-Type header returned by Tornado.
DEFAULT_CONTENT_TYPE = "application/json; charset=UTF-8"


class TestSendHandler(testing.AsyncHTTPTestCase, testing.LogTrapTestCase):

    def setUp(self):
        self.mongodb_client = mongomock.Connection()
        self.dboptions = {
            "dbpassword": "",
            "dbuser": ""
        }
        self.mailoptions = {}

        super(TestSendHandler, self).setUp()

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

        settings = {
            "dboptions": self.dboptions,
            "client": self.mongodb_client,
            "executor": ThreadPoolExecutor(max_workers=2),
            "default_handler_class": AppHandler,
            "master_key": "bar",
            "debug": False,
            "mailoptions": self.mailoptions,
            "senddelay": 60*60
        }

        return web.Application([_SEND_URL], **settings)

    def get_new_ioloop(self):
        return ioloop.IOLoop.instance()

    def test_get(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="GET", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_get_no_token(self):
        response = self.fetch("/send", method="GET")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_delete_no_token(self):
        response = self.fetch("/send", method="DELETE")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_no_token(self):
        response = self.fetch("/send", method="POST", body="")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_missing_job_key(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        body = json.dumps(dict(kernel="kernel"))
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_missing_kernel_key(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        body = json.dumps(dict(job="job"))
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_no_report_specified(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(job="job", kernel="kernel", delay=None)
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    def test_post_boot_report_no_email(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(job="job", kernel="kernel", boot_report=1, delay=None)
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("taskqueue.tasks.send_boot_report")
    def test_post_correct_boot_report(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            boot_report=1, delay=None, boot_send_to="test@example.org")
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                None,
                ["txt"],
                ["test@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=60*60
        )

    def test_post_wrong_delay(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            boot_report=1, boot_send_to="test@example.org", delay="foo"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("taskqueue.tasks.send_boot_report")
    def test_post_negative_delay(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            boot_report=1, boot_send_to="test@example.org", delay=-100
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                None,
                ["txt"],
                ["test@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=100
        )

    @mock.patch("taskqueue.tasks.send_boot_report")
    def test_post_higher_delay(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            boot_report=1, boot_send_to="test@example.org", delay=1000000
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                None,
                ["txt"],
                ["test@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=10800
        )

    @mock.patch("taskqueue.tasks.send_build_report")
    def test_post_build_report_correct(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            build_report=1, build_send_to="test@example.org"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                ["txt"],
                ["test@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=60*60
        )

    def test_post_build_report_no_email(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            build_report=1
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)

    @mock.patch("taskqueue.tasks.send_build_report")
    @mock.patch("taskqueue.tasks.send_boot_report")
    def test_post_build_boot_report_correct(self, mock_boot, mock_build):
        mock_build.apply_async = mock.MagicMock()
        mock_boot.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            build_report=1,
            boot_report=1,
            build_send_to="test@example.org",
            boot_send_to="test2@example.org"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], DEFAULT_CONTENT_TYPE)
        mock_boot.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                None,
                ["txt"],
                ["test2@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=60*60
        )
        mock_build.apply_async.assert_called_with(
            [
                "job",
                "kernel",
                ["txt"],
                ["test@example.org"], self.dboptions, self.mailoptions
            ],
            countdown=60*60
        )

    def test_get_email_addresses_no_addresses(self):
        self.assertListEqual([], sendh._get_email_addresses(None, None))
        self.assertListEqual([], sendh._get_email_addresses('', ''))
        self.assertListEqual([], sendh._get_email_addresses([], []))

    def test_get_email_addresses_only_report(self):
        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses("test@example.org", None))

        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses(["test@example.org"], None))

        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses("test@example.org", ""))

        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses(["test@example.org"], ""))

        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses("test@example.org", []))

        self.assertListEqual(
            ["test@example.org"],
            sendh._get_email_addresses(["test@example.org"], []))

    def test_get_email_addresses_both(self):
        self.assertListEqual(
            ["test@example.org", "test2@example.org"],
            sendh._get_email_addresses(
                "test@example.org", "test2@example.org"))

        self.assertListEqual(
            ["test@example.org", "test2@example.org"],
            sendh._get_email_addresses(
                ["test@example.org"], ["test2@example.org"]))

    def test_check_status(self):
        when = datetime.datetime.now()
        reason, status_code = sendh._check_status(True, True, True, True, when)

        self.assertIsNotNone(reason)
        self.assertEqual(400, status_code)

        reason, status_code = sendh._check_status(
            True, True, True, False, when)

        self.assertIsNotNone(reason)
        self.assertEqual(202, status_code)

        reason, status_code = sendh._check_status(
            True, True, False, True, when)

        self.assertIsNotNone(reason)
        self.assertEqual(202, status_code)

        reason, status_code = sendh._check_status(
            True, True, False, False, when)

        self.assertIsNotNone(reason)
        self.assertEqual(202, status_code)

        reason, status_code = sendh._check_status(
            False, True, False, False, when)

        self.assertIsNotNone(reason)
        self.assertEqual(202, status_code)

        reason, status_code = sendh._check_status(
            False, True, False, True, when)

        self.assertIsNotNone(reason)
        self.assertEqual(400, status_code)

        reason, status_code = sendh._check_status(
            True, False, False, False, when)

        self.assertIsNotNone(reason)
        self.assertEqual(202, status_code)

    def test_email_format(self):
        email_format, errors = sendh._check_email_format(None)

        self.assertListEqual(["txt"], email_format)
        self.assertEqual(0, len(errors))

        email_format, errors = sendh._check_email_format(["html"])

        self.assertListEqual(["html"], email_format)
        self.assertEqual(0, len(errors))

        email_format, errors = sendh._check_email_format(["txt"])

        self.assertListEqual(["txt"], email_format)
        self.assertEqual(0, len(errors))

        email_format, errors = sendh._check_email_format("foo")

        self.assertListEqual(["txt"], email_format)
        self.assertEqual(2, len(errors))

        email_format, errors = sendh._check_email_format(["foo"])

        self.assertListEqual(["txt"], email_format)
        self.assertEqual(2, len(errors))

        email_format, errors = sendh._check_email_format(["html", "txt"])

        self.assertListEqual(["html", "txt"], email_format)
        self.assertEqual(0, len(errors))
