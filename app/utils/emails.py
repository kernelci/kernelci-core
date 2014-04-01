# Copyright (C) 2014 Linaro Ltd.
#
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

"""All email related utilities."""

import smtplib

from email.mime.text import MIMEText

FROM = 'noreply@linaro.org'


def _create_email(job_id):
    msg = MIMEText('')

    msg['Subject'] = 'Results for job: %s' % (job_id)
    msg['From'] = FROM

    return msg


def send(job_id, recipients):

    msg = _create_email(job_id)
    server = smtplib.SMTP('localhost')

    for recipient in recipients:
        msg['To'] = recipient
        server.sendmail(FROM, [recipient], msg.as_string(unixfrom=True))
