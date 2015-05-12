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
import utils.batch.common
import utils.bisect.boot as bootb
import utils.bisect.defconfig as defconfigb
import utils.bootimport
import utils.db
import utils.docimport
import utils.emails
import utils.log_parser
import utils.report.boot
import utils.report.build
import utils.report.common
import utils.tests_import as tests_import


@taskc.app.task(name="import-job")
def import_job(json_obj, db_options, mail_options=None):
    """Just a wrapper around the real import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    job.
    :type json_obj: dictionary
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    """
    return utils.docimport.import_and_save_job(json_obj, db_options)


@taskc.app.task(name="parse-build-log")
def parse_build_log(job_id, json_obj, db_options, mail_options=None):
    """Wrapper around the real build log parsing function.

    Used to provided a task to the import function.

    :param job_id: The ID of the job saved in the database. This value gest
    injected by Celery when linking the task to the previous one.
    :type job_id: string
    :param json_obj: The JSON object with the necessary values.
    :type json_obj: dictionary
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    """
    return utils.log_parser.parse_build_log(job_id, json_obj, db_options)


@taskc.app.task(name="import-boot")
def import_boot(json_obj, db_options, mail_options=None):
    """Just a wrapper around the real boot import function.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    boot report.
    :type json_obj: dictionary
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    """
    return utils.bootimport.import_and_save_boot(json_obj, db_options)


@taskc.app.task(name="batch-executor", ignore_result=False)
def execute_batch(json_obj, db_options):
    """Run batch operations based on the passed JSON object.

    :param json_obj: The JSON object with the operations to perform.
    :type json_obj: dictionary
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return The result of the batch operations.
    """
    return utils.batch.common.execute_batch_operation(json_obj, db_options)


@taskc.app.task(name="boot-bisect", ignore_result=False)
def boot_bisect(doc_id, db_options, fields=None):
    """Run a boot bisect operation on the passed boot document id.

    :param doc_id: The boot document ID.
    :type doc_id: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
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
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the boot bisect operation.
    """
    return bootb.execute_boot_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields)


@taskc.app.task(name="defconfig-bisect", ignore_result=False)
def defconfig_bisect(doc_id, db_options, fields=None):
    """Run a defconfig bisect operation on the passed defconfig document id.

    :param doc_id: The boot document ID.
    :type doc_id: string
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
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
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dictionary
    :return The result of the defconfig bisect operation.
    """
    return defconfigb.execute_defconfig_bisection_compared_to(
        doc_id, compare_to, db_options, fields=fields)


@taskc.app.task(
    name="send-boot-report",
    acks_late=True,
    track_started=True,
    ignore_result=False)
def send_boot_report(job,
                     kernel,
                     lab_name,
                     email_format, to_addrs, db_options, mail_options):
    """Create the boot report email and send it.

    :param job: The job name.
    :type job: string
    :param kernel: The kernel name.
    :type kernel: string
    :param lab_name: The name of the lab.
    :type lab_name: string
    :param email_format: The email format to send.
    :type email_format: list
    :param to_addrs: List of recipients.
    :type to_addrs: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    """
    utils.LOG.info("Preparing boot report email for '%s-%s'", job, kernel)
    status = "ERROR"

    txt_body, html_body, subject, headers = \
        utils.report.boot.create_boot_report(
            job,
            kernel,
            lab_name,
            email_format, db_options=db_options, mail_options=mail_options
        )

    if all([any([txt_body, html_body]), subject]):
        utils.LOG.info("Sending boot report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            to_addrs,
            subject, txt_body, html_body, mail_options, headers=headers)
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
def send_build_report(job,
                      kernel,
                      email_format, to_addrs, db_options, mail_options):
    """Create the build report email and send it.

    :param job: The job name.
    :type job: string
    :param kernel: The kernel name.
    :type kernel: string
    :param email_format: The email format to send.
    :type email_format: list
    :param to_addrs: List of recipients.
    :type to_addrs: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dictionary
    """
    utils.LOG.info("Preparing build report email for '%s-%s'", job, kernel)
    status = "ERROR"

    txt_body, html_body, subject, headers = \
        utils.report.build.create_build_report(
            job,
            kernel,
            email_format,
            db_options=db_options,
            mail_options=mail_options
        )

    if all([any([txt_body, html_body]), subject]):
        utils.LOG.info("Sending build report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            to_addrs,
            subject, txt_body, html_body, mail_options, headers=headers)
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
def complete_test_suite_import(suite_json, suite_id, db_options, **kwargs):
    """Complete the test suite import.

    First update the test suite references, if what is provided is only the
    *_id values. Then, import the test sets and test cases provided.

    :param suite_json: The JSON object with the test suite.
    :type suite_json: dictionary
    :param suite_id: The ID of the test suite.
    :type suite_id: bson.objectid.ObjectId
    :param test_set: The list of test sets to import.
    :type test_set: list
    :param test_case: The list of test cases to import.
    :type test_case: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return 200 if OK, 500 in case of errors; a dictionary containing the
    kwargs passed plus new values take from the update action.
    """
    ret_val, update_doc = tests_import.update_test_suite(
        suite_json, suite_id, db_options, **kwargs)

    # Update all the kwargs with the one taken from the test suite update
    # process and pass them along to the next task.
    kwargs.update(update_doc)

    if ret_val != 200:
        utils.LOG.error(
            "Error updating test suite '%s' (%s)",
            kwargs["suite_name"], suite_id)

    return ret_val, kwargs


@taskc.app.task(
    name="import-sets-from-suite",
    track_started=True,
    ignore_result=False,
    add_to_parent=False)
def import_test_sets_from_test_suite(
        prev_results, suite_id, tests_list, db_options, **kwargs):
    """Import the test sets provided in a test suite.

    This task is linked from the test suite update one: the first argument is a
    list that contains the return values from the previous task. That argument
    is injected once the task has been completed.

    :param prev_results: Injected value that contain the parent task results.
    :type prev_results: list
    :param suite_id: The ID of the suite.
    :type suite_id: bson.objectid.ObjectId
    :pram tests_list: The list of tests to import.
    :type tests_list: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """
    ret_val = 200
    errors = {}

    prev_val = prev_results[0]
    other_args = prev_results[1]

    if all([prev_val == 200, suite_id]):
        test_ids, errors = tests_import.import_multi_test_sets(
            tests_list, suite_id, db_options, **other_args)

        if test_ids:
            utils.LOG.info(
                "Updating test suite '%s' (%s) with test set IDs",
                kwargs["suite_name"], str(suite_id))
            database = utils.db.get_db_connection(db_options)
            ret_val = utils.db.update(
                database[models.TEST_SUITE_COLLECTION],
                suite_id, {models.TEST_SET_KEY: test_ids})
            # TODO: handle errors.
        else:
            ret_val = 500
    else:
        utils.LOG.warn(
            "Error saving test suite '%s', will not import tests cases",
            kwargs["suite_name"])

    return ret_val, errors


@taskc.app.task(
    name="import-cases-from-suite",
    track_started=True,
    ignore_result=False,
    add_to_parent=False)
def import_test_cases_from_test_suite(
        prev_results, suite_id, tests_list, db_options, **kwargs):
    """Import the test cases provided in a test suite.

    This task is linked from the test suite update one: the first argument is a
    list that contains the return values from the previous task. That argument
    is injected once the task has been completed.

    :param prev_results: Injected value that contain the parent task results.
    :type prev_results: list
    :param suite_id: The ID of the suite.
    :type suite_id: bson.objectid.ObjectId
    :pram tests_list: The list of tests to import.
    :type tests_list: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """
    ret_val = 200
    errors = {}

    prev_val = prev_results[0]
    other_args = prev_results[1]

    if all([prev_val == 200, suite_id]):
        test_ids, errors = tests_import.import_multi_test_cases(
            tests_list, suite_id, db_options, **other_args)

        if test_ids:
            utils.LOG.info(
                "Updating test suite '%s' (%s) with test case IDs",
                kwargs["suite_name"], str(suite_id))
            database = utils.db.get_db_connection(db_options)
            ret_val = utils.db.update(
                database[models.TEST_SUITE_COLLECTION],
                suite_id, {models.TEST_CASE_KEY: test_ids})
            # TODO: handle errors.
        else:
            ret_val = 500
    else:
        utils.LOG.warn(
            "Error saving test suite '%s', will not import tests cases",
            kwargs["suite_name"])

    return ret_val, errors


@taskc.app.task(
    name="import-test-cases-from-set", track_started=True, ignore_result=False)
def import_test_cases_from_test_set(
        tests_list, suite_id, set_id, db_options, **kwargs):
    """Wrapper around the real import function.

    Import the test cases included in a test set.

    :param tests_list: The list of test cases to import.
    :type tests_list: list
    :param suite_id: The ID of the test suite.
    :type suite_id: bson.objectid.ObjectId
    :param set_id: The ID of the test set.
    :type set_id: bson.objectid.ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """
    return tests_import.import_test_cases_from_test_set(
        set_id, suite_id, tests_list, db_options, **kwargs)


def run_batch_group(batch_op_list, db_options):
    """Execute a list of batch operations.

    :param batch_op_list: List of JSON object used to build the batch
    operation.
    :type batch_op_list: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
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
