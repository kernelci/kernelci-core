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
import tornado

import handlers.send as sendh

import urls

from handlers.tests.test_handler_base import TestHandlerBase


class TestSendHandler(TestHandlerBase):

    def get_app(self):
        return tornado.web.Application([urls._SEND_URL], **self.settings)

    def test_get(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="GET", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_get_no_token(self):
        response = self.fetch("/send", method="GET")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete(self):
        headers = {"Authorization": "foo"}
        response = self.fetch(
            "/send", method="DELETE", headers=headers)

        self.assertEqual(response.code, 501)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_delete_no_token(self):
        response = self.fetch("/send", method="DELETE")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    def test_post_no_token(self):
        response = self.fetch("/send", method="POST", body="")
        self.assertEqual(response.code, 403)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

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
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.report.send_boot_report")
    def test_post_correct_boot_report(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            git_branch="master",
            boot_report=1, delay=None, send_to="test@example.org")
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                None,
                {
                    "to": ["test@example.org"],
                    "cc": [],
                    "bcc": [],
                    "in_reply_to": None,
                    "subject": None,
                    "format": ["txt"],
                },
            ],
            countdown=60 * 60,
            link=mock.ANY
        )

    def test_post_wrong_delay(self):
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            boot_report=1, send_to="test@example.org", delay="foo"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 400)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)

    @mock.patch("taskqueue.tasks.report.send_boot_report")
    def test_post_negative_delay(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            git_branch="master",
            boot_report=1, send_to="test@example.org", delay=-100
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                None,
                {
                    "format": ["txt"],
                    "to": ["test@example.org"],
                    "cc": [],
                    "bcc": [],
                    "subject": None,
                    "in_reply_to": None,
                },
            ],
            countdown=100,
            link=mock.ANY
        )

    @mock.patch("taskqueue.tasks.report.send_boot_report")
    def test_post_higher_delay(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            git_branch="master",
            boot_report=1, send_to="test@example.org", delay=1000000
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                None,
                {
                    "format": ["txt"],
                    "to": ["test@example.org"],
                    "cc": [],
                    "bcc": [],
                    "subject": None,
                    "in_reply_to": None,
                },
            ],
            countdown=18000,
            link=mock.ANY
        )

    @mock.patch("taskqueue.tasks.report.send_build_report")
    def test_post_build_report_correct(self, mock_schedule):
        mock_schedule.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            git_branch="master",
            build_report=1, send_to="test@example.org"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mock_schedule.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                {
                    "to": ["test@example.org"],
                    "cc": [],
                    "bcc": [],
                    "in_reply_to": None,
                    "subject": None,
                    "format": ["txt"],
                },
            ],
            countdown=60 * 60,
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
            response.headers["Content-Type"], self.content_type)

    def test_check_status(self):
        when = datetime.datetime.now()
        for report_type in ['build', 'boot']:
            for errors in [True, False]:
                reason, status_code = sendh._check_status(
                    report_type, errors, when)
                self.assertIsNotNone(reason)
                self.assertEqual(status_code, 400 if errors else 202)

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
