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
            boot_report=1, delay=None, boot_send_to="test@example.org")
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
                ["txt"],
                ["test@example.org"],
                [],
                [],
                None,
                None
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
            boot_report=1, boot_send_to="test@example.org", delay="foo"
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
            boot_report=1, boot_send_to="test@example.org", delay=-100
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
                ["txt"],
                ["test@example.org"],
                [],
                [],
                None,
                None
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
            boot_report=1, boot_send_to="test@example.org", delay=1000000
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
                ["txt"],
                ["test@example.org"],
                [],
                [],
                None,
                None
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
            build_report=1, build_send_to="test@example.org"
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
                ["txt"],
                ["test@example.org"], self.dboptions,
            ],
            countdown=60 * 60,
            kwargs={
                "cc_addrs": [],
                "bcc_addrs": [], "in_reply_to": None, "subject": None
            }
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

    @mock.patch("taskqueue.tasks.report.send_build_report")
    @mock.patch("taskqueue.tasks.report.send_boot_report")
    def test_post_build_boot_report_correct_with_subject(
            self, mock_boot, mock_build):
        mock_build.apply_async = mock.MagicMock()
        mock_boot.apply_async = mock.MagicMock()
        headers = {
            "Authorization": "foo",
            "Content-Type": "application/json",
        }
        data = dict(
            job="job",
            kernel="kernel",
            git_branch="local/master",
            build_report=1,
            boot_report=1,
            build_send_to="test@example.org",
            boot_send_to="test2@example.org",
            subject="A fake subject"
        )
        body = json.dumps(data)
        response = self.fetch(
            "/send", method="POST", headers=headers, body=body)
        self.assertEqual(response.code, 202)
        self.assertEqual(
            response.headers["Content-Type"], self.content_type)
        mock_boot.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                None,
                ["txt"],
                ["test2@example.org"],
                [],
                [],
                None,
                "A fake subject"
            ],
            countdown=60 * 60,
            link=mock.ANY
        )
        mock_build.apply_async.assert_called_with(
            [
                "job",
                "master",
                "kernel",
                ["txt"],
                ["test@example.org"], self.dboptions,
            ],
            countdown=60 * 60,
            kwargs={
                "cc_addrs": [],
                "bcc_addrs": [],
                "in_reply_to": None, "subject": "A fake subject"
            }
        )

    def test_get_email_addresses_no_addresses(self):
        self.assertTupleEqual(
            ([], [], []), sendh._get_email_addresses(None, None))
        self.assertTupleEqual(([], [], []), sendh._get_email_addresses('', ''))
        self.assertTupleEqual(([], [], []), sendh._get_email_addresses([], []))

    def test_get_email_addresses_only_report(self):
        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses("test@example.org", None))

        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses(["test@example.org"], None))

        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses("test@example.org", ""))

        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses(["test@example.org"], ""))

        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses("test@example.org", []))

        self.assertTupleEqual(
            (["test@example.org"], [], []),
            sendh._get_email_addresses(["test@example.org"], []))

    def test_get_email_addresses_both(self):
        self.assertTupleEqual(
            (["test@example.org", "test2@example.org"], [], []),
            sendh._get_email_addresses(
                "test@example.org", "test2@example.org"))

        self.assertTupleEqual(
            (["test@example.org", "test2@example.org"], [], []),
            sendh._get_email_addresses(
                ["test@example.org"], ["test2@example.org"]))

    def test_get_email_addrs_with_cc_bcc(self):
        self.assertTupleEqual(
            ([], ["test@example.org"], []),
            sendh._get_email_addresses(None, None, cc="test@example.org"))

        self.assertTupleEqual(
            ([], ["test@example.org"], []),
            sendh._get_email_addresses(None, None, cc=["test@example.org"]))

        self.assertTupleEqual(
            ([], ["test@example.org"], ["test@example.org"]),
            sendh._get_email_addresses(
                None, None, cc=["test@example.org"], bcc=["test@example.org"])
        )

        self.assertTupleEqual(
            (
                [],
                ["test@example.org", "test1@example.org"],
                ["test@example.org", "test1@example.org"]
            ),
            sendh._get_email_addresses(
                None, None,
                cc=["test@example.org"], bcc=["test@example.org"],
                g_cc="test1@example.org", g_bcc=["test1@example.org"]
            )
        )

        self.assertTupleEqual(
            (
                [],
                ["test@example.org", "test1@example.org"],
                ["test@example.org", "test1@example.org"]
            ),
            sendh._get_email_addresses(
                None, None,
                cc=["test@example.org"], bcc=["test@example.org"],
                g_cc=["test1@example.org"], g_bcc=["test1@example.org"]
            )
        )

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
