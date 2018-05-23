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

"""Send email."""

import cStringIO
import copy
import email
import email.mime.multipart
import email.mime.text
import smtplib
import types

from email.generator import Generator
from email.header import Header

import models
import utils


def is_ascii(string):
    """Check if a string contains only ASCII characters.

    :param string: The string to check.
    :type string: str
    :return True or False
    """
    ret_val = True
    if isinstance(string, types.StringTypes):
        try:
            string.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            ret_val = False
    return ret_val


def to_unicode(string):
    """Convert a string to unicode.

    :param string: The string to convert.
    :type string: str
    :return A unicode encoded string.
    """
    if all([isinstance(string, types.StringTypes),
            not isinstance(string, types.UnicodeType)]):
        string = unicode(string, "utf-8")
    return string


# pylint: disable=too-many-branches
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def create_email(
        to_addrs,
        from_addr,
        subject,
        txt_body,
        html_body,
        sender_desc=None,
        headers=None, cc_addrs=None, bcc_addrs=None, in_reply_to=None):
    """Create the email message.

    :param to_addrs: A list of email address for the To field.
    :type to_addrs: list
    :param from_addr: The email address for the From field.
    :type from_addr: str
    :param subject: The email subject.
    :type subject: str, unicode
    :param txt_body: The TXT body of the email.
    :type txt_body: str, unicode
    :param html_body: The HTML body of the email.
    :type html_body: str, unicode
    :param sender_desc: The descriptio for the sender email address.
    :type sender_desc: str
    :param headers: Additional headers to set for the emails.
    :type headers: dict
    :param cc_addrs: List of CC email addresses.
    :type cc_addrs: list
    :param bcc_addrs: List of BCC email addresses.
    :type bcc_addrs: list
    :param in_reply_to: The message ID this email should be a reply to.
    :type in_reply_to: str
    :return A 3-tuple: The email message instance; a string with the built
    email message; the list of emails to send the message.
    """
    # Add how to treat charset for emails: Quoted Printable.
    # pylint: disable=no-member
    email.Charset.add_charset(
        "utf-8", email.Charset.QP, email.Charset.QP, "utf-8")

    send_to = copy.deepcopy(to_addrs)

    # Make sure everything is a unicode string.
    subject = to_unicode(subject)
    txt_body = to_unicode(txt_body)
    html_body = to_unicode(html_body)
    from_addr = to_unicode(from_addr)
    sender_desc = to_unicode(sender_desc)
    in_reply_to = to_unicode(in_reply_to)
    to_addrs = [to_unicode(addr) for addr in to_addrs]

    if cc_addrs:
        cc_addrs = [to_unicode(addr) for addr in cc_addrs]
    if bcc_addrs:
        bcc_addrs = [to_unicode(addr) for addr in bcc_addrs]

    if all([txt_body, html_body]):
        msg = email.mime.multipart.MIMEMultipart("alternative")
        txt_msg = email.mime.text.MIMEText(txt_body, "plain", "utf-8")
        html_msg = email.mime.text.MIMEText(html_body, "html", "utf-8")
        msg.attach(txt_msg)
        msg.attach(html_msg)
    elif txt_body:
        msg = email.mime.text.MIMEText(txt_body, "plain", "utf-8")
    elif html_body:
        msg = email.mime.text.MIMEText(html_body, "html", "utf-8")

    if headers:
        for key, val in headers.iteritems():
            val = to_unicode(val)
            if is_ascii(val):
                msg[key] = str(val)
            else:
                msg[key] = Header(val, "utf-8").encode()

    if in_reply_to:
        msg["In-Reply-To"] = msg["References"] = in_reply_to

    if is_ascii(subject):
        msg["Subject"] = subject
    else:
        msg["Subject"] = Header(subject, "utf-8").encode()

    msg["To"] = u", ".join(send_to)

    if sender_desc:
        if is_ascii(sender_desc):
            from_str = u"{:s} <{:s}>".format(sender_desc, from_addr)
        else:
            # Only the description needs to be encoded, not the email.
            from_str = u"{:s} <{:s}>".format(
                Header(sender_desc, "utf-8").encode(), from_addr)
    else:
        from_str = from_addr

    msg["From"] = from_str

    if cc_addrs:
        send_to.extend(cc_addrs)
        msg["Cc"] = u", ".join(cc_addrs)
    if bcc_addrs:
        send_to.extend(bcc_addrs)

    msg_out = cStringIO.StringIO()
    gen = Generator(msg_out, False)
    gen.flatten(msg)

    return msg, msg_out.getvalue(), send_to


def send_email(subject, txt_body, html_body, email_opts, config, headers=None):
    """Send email to the specified address.

    :param subject: The email subject.
    :type subject: str, unicode
    :param txt_body: The email body in TXT format.
    :type txt_body: str, unicode
    :param html_body: The email body in HTML.
    :type html_body: str, unicode
    :param email_opts: The email options such as to/cc/in-reply-to.
    :type email_opts: dict
    :param config: The email config data structure.
    :type config: dict
    :param headers: Extra custom email headers
    :type headers: dict
    :return A tuple with the status and a list of errors.
    """
    errors = []
    status = models.ERROR_STATUS

    m_get = config.get
    port = m_get("smtp_port", None)
    host = m_get("smtp_host", None)
    user = m_get("smtp_user", None)
    password = m_get("smtp_password", None)
    from_addr = m_get("smtp_sender", None)
    sender_desc = m_get("smtp_sender_desc", None)

    _, email_msg, send_to = create_email(
        email_opts["to"],
        from_addr,
        subject,
        txt_body,
        html_body,
        sender_desc=sender_desc,
        headers=headers,
        cc_addrs=email_opts.get("cc"),
        bcc_addrs=email_opts.get("bcc"),
        in_reply_to=email_opts.get("in_reply_to")
    )

    if all([from_addr, host]):
        server = None
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port=port)
            else:
                server = smtplib.SMTP(host, port=port)

            if all([user, password]):
                server.login(user, password)

            server.sendmail(from_addr, send_to, email_msg)
            status = models.SENT_STATUS
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError), ex:
            utils.LOG.error("SMTP conn/auth error")
            errors.append((ex.smtp_code, ex.smtp_error))
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused), ex:
            utils.LOG.error(
                "Error sending email: recipients or sender refused")
            errors.append((ex.smtp_code, ex.smtp_error))
        except (smtplib.SMTPHeloError, smtplib.SMTPDataError), ex:
            utils.LOG.error("SMTP server error")
            errors.append((ex.smtp_code, ex.smtp_error))
        except smtplib.SMTPException, ex:
            utils.LOG.error("Generic SMTP error: no auth method, ...")
            errors.append((ex.smtp_code, ex.smtp_error))
        except Exception, ex:
            utils.LOG.exception(ex)
            utils.LOG.error(
                "Unexpected SMTP error: %s", str(ex))
            errors.append((500, str(ex)))
        finally:
            if server is not None:
                server.quit()
    else:
        errors.append(
            (500, "No STMP host and/or sender specified: no email sent"))
        utils.LOG.error(
            "Cannot send emails: no SMTP host and/or sender specified")

    return status, errors
