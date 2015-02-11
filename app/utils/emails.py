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

import email
import smtplib

import models
import utils


# pylint: disable=too-many-branches
def send_email(to_addrs, subject, body, mail_options):
    """Send email to the specified address.

    :param to_addrs: The recipients address.
    :type to_addrs: list
    :param subject: The email subject.
    :type subject: str
    :param body: The email body.
    :type body: str, unicode
    :param mail_options: The email options data structure.
    :type mail_options: dict
    :return A tuple with the status and a list of errors.
    """
    errors = []
    status = models.ERROR_STATUS

    msg = email.mime.text.MIMEText(body, _charset="utf_8")
    msg["Subject"] = subject

    m_get = mail_options.get
    port = m_get("port")
    host = m_get("host")
    user = m_get("user")
    password = m_get("password")
    from_addr = m_get("sender")
    sender_desc = m_get("sender_desc", None)

    msg["To"] = ", ".join(to_addrs)
    if sender_desc:
        msg["From"] = "%s <%s>" % (sender_desc, from_addr)
    else:
        msg["From"] = from_addr

    if all([from_addr, host]):
        server = None
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(host, port=port)
            else:
                server = smtplib.SMTP(host, port=port)

            if all([user, password]):
                server.login(user, password)

            server.sendmail(from_addr, to_addrs, msg.as_string())
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
            utils.LOG.error(
                "Unexpected SMTP error: %s - %s", ex.errno, ex.strerror)
            utils.LOG.exception(ex)
            errors.append((ex.errno, ex.strerror))
        finally:
            if server is not None:
                server.quit()
    else:
        utils.LOG.error(
            "Cannot send emails: no SMTP host and/or sender specified")

    return status, errors
