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

"""All reports related celery tasks."""

import models
import taskqueue.celery as taskc
import utils.db
import utils.emails
import utils.report.boot
import utils.report.build
import utils.report.common
import utils.report.error


# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=too-many-locals
@taskc.app.task(name="send-boot-report")
def send_boot_report(job, git_branch, kernel, lab_name, email_opts):
    """Create the boot report email and send it.

    :param job: The job name.
    :type job: string
    :param kernel: The kernel name.
    :type kernel: string
    :param lab_name: The name of the lab.
    :type lab_name: string
    :param email_opts: Email options.
    :type email_opts: dict
    """
    report_id = "-".join([job, git_branch, kernel])
    utils.LOG.info("Preparing boot report email for '{}'".format(report_id))
    status = "ERROR"

    db_options = taskc.app.conf.get("db_options", {})

    txt_body, html_body, new_subject, headers = \
        utils.report.boot.create_boot_report(
            job,
            git_branch,
            kernel,
            lab_name,
            email_opts["format"],
            db_options=db_options,
            mail_options=taskc.app.conf.get("mail_options", None)
        )

    subject = email_opts.get("subject") or new_subject

    if (txt_body or html_body) and subject:
        utils.LOG.info("Sending boot report email for '{}'".format(report_id))
        status, errors = utils.emails.send_email(
            subject, txt_body, html_body, email_opts,
            taskc.app.conf.mail_options, headers
        )
        utils.report.common.save_report(
            job, git_branch, kernel, models.BOOT_REPORT,
            status, errors, db_options
        )
    else:
        utils.LOG.error(
            "No email body nor subject found for boot report '{}'"
            .format(report_id))

    return status


@taskc.app.task(name="trigger-bisections")
def trigger_bisections(status, job, branch, kernel, lab_name):
    report_id = "-".join([job, branch, kernel])
    utils.LOG.info("Triggering bisections for '{}'".format(report_id))
    return utils.report.boot.trigger_bisections(
        status,
        job,
        branch, kernel, lab_name,
        taskc.app.conf.get("db_options", {}),
        taskc.app.conf.get("jenkins_options", None))


@taskc.app.task(name="send-build-report")
def send_build_report(job, git_branch, kernel, email_opts):
    """Create the build report email and send it.

    :param job: The job name.
    :type job: string
    :param git_branch: The git branch name.
    :type git_branch: string
    :param kernel: The kernel name.
    :type kernel: string
    :param email_opts: Email options.
    :type email_opts: dict
    """
    utils.LOG.info(
        "Preparing build report email for '%s-%s-%s'", job, git_branch, kernel)
    status = "ERROR"

    db_options = taskc.app.conf.get("db_options", {})

    txt_body, html_body, new_subject, headers = \
        utils.report.build.create_build_report(
            job,
            git_branch,
            kernel,
            email_opts["format"],
            db_options=db_options,
            mail_options=taskc.app.conf.get("mail_options", None)
        )

    subject = email_opts.get("subject") or new_subject

    if (txt_body or html_body) and subject:
        utils.LOG.info("Sending build report email for '%s-%s'", job, kernel)
        status, errors = utils.emails.send_email(
            subject, txt_body, html_body, email_opts,
            taskc.app.conf.mail_options, headers
        )
        utils.report.common.save_report(
            job, git_branch, kernel, models.BUILD_REPORT,
            status, errors, db_options
        )
    else:
        utils.LOG.error(
            "No email body nor subject found for build report '{}-{}-{}'"
            .format(job, git_branch, kernel))

    return status


@taskc.app.task(name="send-multi-email-errors-report")
def send_multiple_emails_error(
        job, git_branch, kernel, date, email_format, email_type, data):

    email_data = {
        "job": job,
        "git_branch": git_branch,
        "kernel": kernel,
        "trigger_time": date,
        "email_format": email_format,
        "email_type": email_type,
        "to_addrs": data.get("to"),
        "cc_addrs": data.get("cc"),
        "subject": data.get("subject"),
        "in_reply_to": data.get("in_reply_to"),
        "trigger_time": date
    }

    db = utils.db.get_db_connection2(taskc.app.conf.db_options)
    result = utils.db.find_one2(
        db[models.JOB_COLLECTION],
        {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.GIT_BRANCH_KEY: git_branch
        },
        [
            models.GIT_COMMIT_KEY,
            models.GIT_DESCRIBE_V_KEY,
            models.KERNEL_VERSION_KEY,
            models.GIT_URL_KEY
        ])

    if result:
        email_data.update(result)

    txt_body, html_body, subject = \
        utils.report.error.create_duplicate_email_report(email_data)

    if (txt_body or html_body) and subject:
        utils.LOG.info(
            "Sending duplicate emails report for %s-%s-%s",
            job, git_branch, kernel)
        email_opts = {"to": [taskc.app.conf.mail_options["error_email"]]}
        utils.emails.send_email(subject, txt_body, html_body, email_opts,
                                taskc.app.conf.mail_options)
