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

import celery
import types

import models
import taskqueue.celery as taskc
import utils
import utils.batch.common
import utils.bisect
import utils.bootimport
import utils.docimport
import utils.emails
import utils.report


@taskc.app.task(name='send-emails', ignore_result=True)
def send_emails(job_id):
    """Just a wrapper around the real `send` function.

    This is used to provide a Celery-task access to the underlying function.

    :param job_id: The job ID to trigger notifications for.
    """
    # send(job_id)
    # XXX: This has been removed since the subscription handler is not used
    # right now and will be completely reworked in the future.
    pass


@taskc.app.task(name="import-job")
def import_job(json_obj, db_options):
    """Just a wrapper around the real import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
        job.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    utils.docimport.import_and_save_job(json_obj, db_options)


@taskc.app.task(name="import-boot")
def import_boot(json_obj, db_options):
    """Just a wrapper around the real boot import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    boot report.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    utils.bootimport.import_and_save_boot(json_obj, db_options)


@taskc.app.task(name="batch-executor", ignore_result=False)
def execute_batch(json_obj, db_options):
    """Run batch operations based on the passed JSON object.

    :param json_obj: The JSON object with the operations to perform.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return The result of the batch operations.
    """
    return utils.batch.common.execute_batch_operation(json_obj, db_options)


@taskc.app.task(name="boot-bisect", ignore_result=False)
def boot_bisect(doc_id, db_options, fields=None):
    """Run a boot bisect operation on the passed boot document id.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The result of the boot bisect operation.
    """
    return utils.bisect.execute_boot_bisection(doc_id, db_options, fields)


@taskc.app.task(name="defconfig-bisect", ignore_result=False)
def defconfig_bisect(doc_id, db_options, fields=None):
    """Run a defconfig bisect operation on the passed defconfig document id.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The result of the boot bisect operation.
    """
    return utils.bisect.execute_defconfig_bisection(doc_id, db_options, fields)


@taskc.app.task(
    name="schedule-boot-report",
    acks_late=True,
    track_started=True)
def schedule_boot_report(json_obj, db_options, mail_options, countdown):
    """Schedule a second task to send the boot report.

    :param json_obj: The json data as sent in the request.
    :type json_obj: dict
    :param db_options: The options necessary to connect to the database.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    :param countdown: The delay in seconds to send the email.
    :type countdown: int
    """
    j_get = json_obj.get
    to_addrs = []

    if bool(j_get(models.SEND_BOOT_REPORT_KEY, False)):
        job = j_get(models.JOB_KEY)
        kernel = j_get(models.KERNEL_KEY)
        lab_name = j_get(models.LAB_NAME_KEY, None)

        boot_emails = j_get(models.BOOT_REPORT_SEND_TO_KEY, None)
        generic_emails = j_get(models.REPORT_SEND_TO_KEY, None)

        if boot_emails is not None:
            if isinstance(boot_emails, types.ListType):
                to_addrs.extend(boot_emails)
            elif isinstance(boot_emails, types.StringTypes):
                to_addrs.append(boot_emails)

        if generic_emails is not None:
            if isinstance(generic_emails, types.ListType):
                to_addrs.extend(generic_emails)
            elif isinstance(generic_emails, types.StringTypes):
                to_addrs.append(generic_emails)

        if to_addrs:
            send_boot_report.apply_async(
                [job, kernel, lab_name, to_addrs, db_options, mail_options],
                countdown=countdown)
        else:
            utils.LOG.warn(
                "No send email addresses specified for '%s-%s': boot report "
                "cannot be sent", job, kernel)


@taskc.app.task(
    name="send-boot-report",
    acks_late=True,
    track_started=True,
    ignore_result=False)
def send_boot_report(job, kernel, lab_name, to_addrs, db_options, mail_options):
    """Create the boot report email and send it.

    :param job: The job name.
    :type job: str
    :param kernel: The kernel name.
    :type kernel: str
    :param lab_name: The name of the lab.
    :type lab_name: str
    :param to_addrs: List of recipients.
    :type to_addrs: list
    :param db_options: The options necessary to connect to the database.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    """
    utils.LOG.info("Preparing boot report email for '%s-%s'", job, kernel)
    status = 400

    body, subject = utils.report.create_boot_report(
        job, kernel, lab_name, db_options=db_options)

    if all([body is not None, subject is not None]):
        utils.LOG.info("Sending boot report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            to_addrs, subject, body, mail_options)
        utils.report.save_report(
            job, kernel, models.BOOT_REPORT, status, errors, db_options)
    return status


def run_batch_group(batch_op_list, db_options):
    """Execute a list of batch operations.

    :param batch_op_list: List of JSON object used to build the batch
    operation.
    :type batch_op_list: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    job = celery.group(
        [
            execute_batch.s(batch_op, db_options)
            for batch_op in batch_op_list
        ]
    )
    result = job.apply_async()
    while not result.ready():
        pass
    return result.get()
