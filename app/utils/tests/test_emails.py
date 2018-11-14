# -*- coding: utf-8 -*-
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

import mock
import unittest
import logging

from email.header import Header

import utils.emails


class TestEmails(unittest.TestCase):

    def setUp(self):
        self.from_addr = "from@example.net"
        self.to_addrs = ["to0@example.net"]
        self.cc_addrs = ["cc0@example.net"]
        self.bcc_addrs = ["bcc0@example.net"]
        self.ascii_subject = "An ASCII email subject"
        self.ascii_txt_body = "Some ASCII text"
        self.ascii_html_body = "<html>Some ASCII fake-HTML</html>"
        self.unicode_subject = u"A sùbjèçt with «Ũnicode» characters ♡⚐☮"

    def test_is_ascii(self):
        self.assertTrue(utils.emails.is_ascii(""))
        self.assertTrue(utils.emails.is_ascii("foo"))
        self.assertTrue(utils.emails.is_ascii(u"foobar"))
        self.assertTrue(utils.emails.is_ascii(012345))

        self.assertFalse(utils.emails.is_ascii(u"èàìòù"))
        self.assertFalse(utils.emails.is_ascii(u"fooò"))
        self.assertFalse(utils.emails.is_ascii("èàìòù"))
        self.assertFalse(utils.emails.is_ascii(u"Ȧå✄♡♢☇…¿foo×±"))

    def test_to_unicode(self):
        self.assertIsInstance(utils.emails.to_unicode("foo"), unicode)
        self.assertIsInstance(utils.emails.to_unicode(u"foo"), unicode)
        self.assertIsInstance(utils.emails.to_unicode(u"èàìòù"), unicode)
        self.assertIsInstance(utils.emails.to_unicode("èàìòù"), unicode)

    def test_create_txt_email_ascii_no_headers_no_other_addrs(self):
        msg, _, send_to = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            sender_desc="Sender Email"
        )
        expected_addrs = ["to0@example.net"]

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual("to0@example.net", msg["To"])
        self.assertEqual("\"Sender Email\" <from@example.net>", msg["From"])
        self.assertEqual("An ASCII email subject", msg["Subject"])
        self.assertListEqual(expected_addrs, send_to)

    def test_create_txt_email_ascii_no_sender_desc(self):
        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None
        )

        self.assertEqual("from@example.net", msg["From"])

    def test_create_txt_email_ascii_no_headers_other_addrs(self):
        msg, _, send_to = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            sender_desc="Sender Email",
            cc_addrs=self.cc_addrs, bcc_addrs=self.bcc_addrs
        )
        expected_addrs = [
            "to0@example.net",
            "cc0@example.net",
            "bcc0@example.net"
        ]

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual("cc0@example.net", msg["Cc"])
        self.assertListEqual(expected_addrs, send_to)

    def test_create_html_email_ascii_no_headers(self):
        msg, _, send_to = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            None,
            self.ascii_html_body
        )

        self.assertEqual("text/html; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])

    def test_create_txt_html_email_ascii_no_headers(self):
        msg, _, send_to = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            self.ascii_html_body
        )

        self.assertTrue(
            msg["Content-Type"].startswith("multipart/alternative; boundary="))

    def test_create_txt_email_multiple_to(self):
        self.to_addrs.append("to1@example.net")
        self.cc_addrs.append("cc1@example.net")

        msg, _, send_to = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            cc_addrs=self.cc_addrs, bcc_addrs=self.bcc_addrs
        )
        expected_addrs = [
            "to0@example.net",
            "to1@example.net",
            "cc0@example.net",
            "cc1@example.net",
            "bcc0@example.net"
        ]

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual("cc0@example.net, cc1@example.net", msg["Cc"])
        self.assertEqual("to0@example.net, to1@example.net", msg["To"])
        self.assertListEqual(expected_addrs, send_to)

    def test_create_txt_email_with_headers(self):
        headers = {
            "X-Kernelci-FakeHeader-0": "foo",
            "X-Kernelci-FakeHeader-1": "bar",
        }

        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            headers=headers
        )

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual("foo", msg["X-Kernelci-FakeHeader-0"])
        self.assertEqual("bar", msg["X-Kernelci-FakeHeader-1"])

    def test_create_txt_email_with_headers_unicode(self):
        header_val0 = u"fòóõŏ"
        header_val1 = u"báãåāȓ"
        headers = {
            "X-Kernelci-FakeHeader-0": header_val0,
            "X-Kernelci-FakeHeader-1": header_val1,
            "X-Kernelci-FakeHeader-2": 1234567890,
        }

        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            headers=headers
        )

        expected_header0 = Header(header_val0, "utf-8")
        expected_header1 = Header(header_val1, "utf-8")

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual(expected_header0, msg["X-Kernelci-FakeHeader-0"])
        self.assertEqual(expected_header1, msg["X-Kernelci-FakeHeader-1"])
        self.assertEqual("1234567890", msg["X-Kernelci-FakeHeader-2"])

    def test_create_txt_email_in_reply_to(self):
        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.ascii_subject,
            self.ascii_txt_body,
            None,
            in_reply_to="messageid"
        )

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual("messageid", msg["In-Reply-To"])
        self.assertEqual("messageid", msg["References"])

    def test_create_txt_email_unicode_subject(self):
        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.unicode_subject,
            self.ascii_txt_body,
            None
        )

        expected_subject = Header(self.unicode_subject, "utf-8").encode()

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual(expected_subject, msg["Subject"])

    def test_create_txt_email_unicode_sender_desc(self):
        sender_desc = u"My èṁàìl"
        msg, _, _ = utils.emails.create_email(
            self.to_addrs,
            self.from_addr,
            self.unicode_subject,
            self.ascii_txt_body,
            None,
            sender_desc=sender_desc
        )

        expected_from = u"\"{:s}\" <{:s}>".format(
            Header(sender_desc, "utf-8").encode(), self.from_addr)

        self.assertEqual("text/plain; charset=\"utf-8\"", msg["Content-Type"])
        self.assertEqual("quoted-printable", msg["Content-Transfer-Encoding"])
        self.assertEqual(expected_from, msg["From"])


class TestEmailsSend(unittest.TestCase):

    def setUp(self):
        super(TestEmailsSend, self).setUp()
        logging.disable(logging.CRITICAL)

        self.mail_options = {
            "smtp_port": 465,
            "smtp_host": "localhost",
            "smtp_user": "mailuser",
            "smtp_password": "mailpassword",
            "smtp_sender": "me@example.net",
            "smtp_sender_desc": "Me Email"
        }

        self.to_addrs = ["to0@example.net"]

        ssl_server_patcher = mock.patch("smtplib.SMTP_SSL")
        patched_ssl_server = ssl_server_patcher.start()
        patched_ssl_server.sendmail = mock.MagicMock()
        patched_ssl_server.login = mock.MagicMock()

        self.addCleanup(ssl_server_patcher.stop)

        server_patcher = mock.patch("smtplib.SMTP")
        patched_server = server_patcher.start()
        patched_server.sendmail = mock.MagicMock()
        patched_server.login = mock.MagicMock()

        self.addCleanup(server_patcher.stop)

        create_email_patcher = mock.patch("utils.emails.create_email")
        self.mock_create_email = create_email_patcher.start()

        self.addCleanup(create_email_patcher.stop)

    def tearDown(self):
        super(TestEmailsSend, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_send_email_no_mail_options(self):
        self.mock_create_email.return_value = (None, None, None)

        email_opts = {"to": self.to_addrs}
        status, errors = utils.emails.send_email(
            "subject", "txt-body", "html-body", email_opts, {})

        self.assertEqual("ERROR", status)
        self.assertEqual(1, len(errors))

    def test_send_email_simple(self):
        self.mock_create_email.return_value = (None, "Message", [])

        email_opts = {"to": self.to_addrs}
        status, errors = utils.emails.send_email(
            "subject", "txt-body", "html-body", email_opts, self.mail_options)

        self.assertEqual("SENT", status)
        self.assertListEqual([], errors)

    def test_send_email_simple_no_ssl(self):
        self.mail_options["port"] = 25
        self.mock_create_email.return_value = (None, "Message", [])

        email_opts = {"to": self.to_addrs}
        status, errors = utils.emails.send_email(
            "subject", "txt-body", "html-body", email_opts, self.mail_options)

        self.assertEqual("SENT", status)
        self.assertListEqual([], errors)
