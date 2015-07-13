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
import email
import email.mime.multipart
import email.mime.text
import smtplib

from email.generator import Generator
from email.header import Header

import models
import utils


def _is_ascii(string):
    """Check if a string contains only ASCII characters.

    :param string: The string to check.
    :type string: string
    :return True or False
    """
    ret_val = True
    try:
        string.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        ret_val = False
    return ret_val


# pylint: disable=too-many-branches
def send_email(to_addrs,
               subject,
               txt_body,
               html_body,
               mail_options,
               headers=None, cc=None, bcc=None, in_reply_to=None):
    """Send email to the specified address.

    :param to_addrs: The recipients address.
    :type to_addrs: list
    :param subject: The email subject.
    :type subject: string
    :param txt_body: The email body in TXT format.
    :type txt_body: string, unicode
    :param html_body: The email body in HTML.
    :type html_body: string, unicode
    :param mail_options: The email options data structure.
    :type mail_options: dict
    :param cc: The list of addresses to add in CC.
    :type cc: list
    :param bcc: The list of addresses to add in BCC.
    :type bcc: list
    :param in_reply_to: The ID of the message this email is a reply to.
    :type in_reply_to: string
    :return A tuple with the status and a list of errors.
    """
    errors = []
    status = models.ERROR_STATUS
    email.Charset.add_charset(
        "utf-8", email.Charset.QP, email.Charset.QP, "utf-8")

    if all([txt_body, html_body]):
        msg = email.mime.multipart.MIMEMultipart("alternative")
        txt_msg = email.mime.text.MIMEText(
            txt_body.encode("utf-8"), "plain", "utf-8")
        html_msg = email.mime.text.MIMEText(
            html_body.encode("utf-8"), "html", "utf-8")
        msg.attach(txt_msg)
        msg.attach(html_msg)
    elif txt_body:
        msg = email.mime.text.MIMEText(
            txt_body.encode("utf-8"), "plain", "utf-8")
    elif html_body:
        msg = email.mime.text.MIMEText(
            html_body.encode("utf-8"), "html", "utf-8")

    if headers:
        for key, val in headers.iteritems():
            if _is_ascii(val):
                msg[key] = str(val)
            else:
                msg[key] = Header(val.encode("utf-8"), "UTF-8").encode()

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to.encode("utf-8")
        msg["References"] = in_reply_to.encode("utf-8")

    if _is_ascii(subject):
        msg["Subject"] = subject.encode("utf-8")
    else:
        msg["Subject"] = Header(subject.encode("utf-8"), "UTF-8").encode()

    m_get = mail_options.get
    port = m_get("port")
    host = m_get("host")
    user = m_get("user")
    password = m_get("password")
    from_addr = m_get("sender")
    sender_desc = m_get("sender_desc", None)

    to_str = u", ".join(to_addrs)
    msg["To"] = to_str.encode("utf-8")

    if sender_desc:
        from_str = u"{:s} <{:s}>".format(sender_desc, from_addr)
    else:
        from_str = from_addr

    if _is_ascii(from_str):
        msg["From"] = from_str.encode("utf-8")
    else:
        msg["From"] = Header(from_str.encode("utf-8"), "UTF-8").encode()

    if cc:
        to_addrs.extend(cc)
        cc_str = u", ".join(cc)
        msg["Cc"] = cc_str.encode("utf-8")
    if bcc:
        to_addrs.extend(bcc)

    msg_out = cStringIO.StringIO()
    gen = Generator(msg_out, False)
    gen.flatten(msg)

    if all([from_addr, host]):
        server = None
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port=port)
            else:
                server = smtplib.SMTP(host, port=port)

            if all([user, password]):
                server.login(user, password)

            server.sendmail(from_addr, to_addrs, msg_out.getvalue())
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
        utils.LOG.error(
            "Cannot send emails: no SMTP host and/or sender specified")

    return status, errors
