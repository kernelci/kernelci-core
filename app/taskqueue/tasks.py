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

from __future__ import absolute_import

from celery import group

from taskqueue.celery import app
from utils.bootimport import import_and_save_boot
from utils.docimport import import_and_save_job
from utils.subscription import send
from utils.batch.common import (
    execute_batch_operation,
)
from utils import LOG


@app.task(name='send-emails', ignore_result=True)
def send_emails(job_id):
    """Just a wrapper around the real `send` function.

    This is used to provide a Celery-task access to the underlying function.

    :param job_id: The job ID to trigger notifications for.
    """
    send(job_id)


@app.task(name='import-job', ignore_result=True)
def import_job(json_obj, db_options):
    """Just a wrapper around the real import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
        job.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    import_and_save_job(json_obj, db_options)


@app.task(name='import-boot', ignore_result=True)
def import_boot(json_obj, db_options):
    """Just a wrapper around the real boot import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    boot report.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    import_and_save_boot(json_obj, db_options)


@app.task(name='batch-executor')
def execute_batch(json_obj, db_options):
    """Run batch operations based on the passed JSON object.

    :param json_obj: The JSON object with the operations to perform.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return The result of the batch operations.
    """
    return execute_batch_operation(json_obj, db_options)


def run_batch_group(batch_op_list, db_options):
    """Execute a list of batch operations.

    :param batch_op_list: List of JSON object used to build the batch
    operation.
    :type batch_op_list: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    job = group(
        [
            execute_batch.s(batch_op, db_options)
            for batch_op in batch_op_list
        ]
    )
    result = job.apply_async()
    while not result.ready():
        pass
    return result.get()
