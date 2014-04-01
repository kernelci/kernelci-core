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

"""Tasks that should be run via Celery."""

from celeryqueue.celery import app
from utils.subscription import send


@app.task(name='send-emails')
def send_emails(job_id):
    """Just a wrapper around the real `send` function.

    This is used to provide a Celery-task access to the underlying function.

    :param job_id: The job ID to trigger notifications for.
    """
    send(job_id)
