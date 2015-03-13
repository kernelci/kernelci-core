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

import models
import taskqueue.celery as taskc
import utils
import utils.db
import utils.batch.common
import utils.bisect.boot as bootb
import utils.bisect.defconfig as defconfigb
import utils.bootimport
import utils.docimport
import utils.emails
import utils.report.boot
import utils.report.build
import utils.report.common
import utils.tests_import as tests_import


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
    return bootb.execute_boot_bisection(doc_id, db_options, fields=fields)


@taskc.app.task(name="boot-bisect-compare-to", ignore_result=False)
def boot_bisect_compared_to(doc_id, compare_to, db_options, fields=None):
    """Run a boot bisect operation compared to the provided tree name.

    :param doc_id: The boot document ID.
    :type doc_id: string
    :param compare_to: The name of the tree to compare to.
    :type compare_to: string
    :param db_options: The mongodb database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The result of the boot bisect operation.
    """
    return bootb.execute_boot_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields)


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
    return defconfigb.execute_defconfig_bisection(
        doc_id, db_options, fields=fields)


@taskc.app.task(name="defconfig-bisect-compared-to", ignore_result=False)
def defconfig_bisect_compared_to(doc_id, compare_to, db_options, fields=None):
    """Run a defconfig bisect operation compared to the provided tree name.

    :param doc_id: The defconfig document ID.
    :type doc_id: string
    :param compare_to: The name of the tree to compare to.
    :type compare_to: string
    :param db_options: The mongodb database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The result of the defconfig bisect operation.
    """
    return defconfigb.execute_defconfig_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields
    )


@taskc.app.task(
    name="send-boot-report",
    acks_late=True,
    track_started=True,
    ignore_result=False)
def send_boot_report(job,
                     kernel, lab_name, to_addrs, db_options, mail_options):
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
    status = "ERROR"

    body, subject = utils.report.boot.create_boot_report(
        job,
        kernel,
        lab_name,
        db_options=db_options,
        mail_options=mail_options
    )

    if all([body is not None, subject is not None]):
        utils.LOG.info("Sending boot report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            to_addrs, subject, body, mail_options)
        utils.report.common.save_report(
            job, kernel, models.BOOT_REPORT, status, errors, db_options)
    else:
        utils.LOG.error(
            "No email body nor subject found for boot report '%s-%s'",
            job, kernel)

    return status


@taskc.app.task(
    name="send-build-report",
    acks_late=True,
    track_started=True,
    ignore_result=False)
def send_build_report(job, kernel, to_addrs, db_options, mail_options):
    """Create the build report email and send it.

    :param job: The job name.
    :type job: str
    :param kernel: The kernel name.
    :type kernel: str
    :param to_addrs: List of recipients.
    :type to_addrs: list
    :param db_options: The options necessary to connect to the database.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    """
    utils.LOG.info("Preparing build report email for '%s-%s'", job, kernel)
    status = "ERROR"

    body, subject = utils.report.build.create_build_report(
        job,
        kernel,
        db_options=db_options,
        mail_options=mail_options
    )

    if all([body is not None, subject is not None]):
        utils.LOG.info("Sending build report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            to_addrs, subject, body, mail_options)
        utils.report.common.save_report(
            job, kernel, models.BOOT_REPORT, status, errors, db_options)
    else:
        utils.LOG.error(
            "No email body nor subject found for build report '%s-%s'",
            job, kernel)

    return status


@taskc.app.task(
    name="complete-test-suite-import",
    track_started=True,
    ignore_result=False)
def complete_test_suite_import(
        suite_json, test_suite_id, test_set, test_case, db_options, **kwargs):
    """Complete the test suite import.

    First update the test suite references, if what is provided is only the
    *_id values. Then, import the test sets and test cases provided.

    :param suite_json: The JSON object with the test suite.
    :type suite_json: dict
    :param test_suite_id: The ID of the test suite.
    :type test_suite_id: string
    :param test_set: The list of test sets to import.
    :type test_set: list
    :param test_case: The list of test cases to import.
    :type test_case: list
    :param db_options: The database connection parameters.
    :type db_options: dict
    """
    k_get = kwargs.get
    suite_name = k_get("suite_name")

    ret_val, update_doc = tests_import.update_test_suite(
        suite_json, test_suite_id, db_options, **kwargs)

    if ret_val != 200:
        utils.LOG.error(
            "Error updating test suite '%s' (%s)", suite_name, test_suite_id)

    kwargs.update(update_doc)

    if test_set:
        # TODO: import test sets.
        pass

    if test_case:
        # TODO: have to wait here for the test case ids and update the test
        # suite.
        import_test_cases.apply_async(
            [
                test_case, test_suite_id, suite_name, db_options
            ],
            kwargs=kwargs
        )


@taskc.app.task(
    name="import-test-cases", track_started=True, ignore_result=False)
def import_test_cases(
        case_list, test_suite_id, test_suite_name, db_options, **kwargs):
    """Import the test cases.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * defconfig_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param case_list: The list with the test cases to import.
    :type case_list: list
    :param test_suite_id: The ID of the test suite these test cases belong to.
    :type test_suite_id: string
    :param test_suite_name: The name of the test suite these test cases belong
    to.
    :type test_suite_name: string
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    """
    utils.LOG.info(
        "Importing test cases for test suite '%s' (%s)",
        test_suite_name, test_suite_id)

    return tests_import.import_multi_test_case(
        case_list, test_suite_id, db_options, **kwargs)


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
