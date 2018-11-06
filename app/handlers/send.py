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

"""This module is used to send boot, build and test report emails."""

import bson
import copy
import datetime
import hashlib
import redis
import types

import handlers.base as hbase
import handlers.response as hresponse
import models
import taskqueue.tasks.report as taskq
import utils

# Max delay in sending email report set to 5hrs.
MAX_DELAY = 18000

TRIGGER_RECEIVED = "Email trigger received from '%s' for '%s-%s-%s' at %s (%s)"
TRIGGER_RECEIVED_ALREADY = "Email trigger for '%s-%s-%s' (%s) already received"
ERR_409_MESSAGE = "Email request already registered"

REPORT_TYPE_KEYS = {
    'build': [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
    ],
    'boot': [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
        models.LAB_NAME_KEY,
    ],
    'bisect': [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
        models.TYPE_KEY,
        models.ARCHITECTURE_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.LAB_NAME_KEY,
        models.BISECT_LOG_KEY,
        models.DEVICE_TYPE_KEY,
        models.BISECT_GOOD_COMMIT_KEY,
        models.BISECT_BAD_COMMIT_KEY,
    ],
    'test': [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
        models.PLANS_KEY,
    ],
}


# pylint: disable=too-many-public-methods
class SendHandler(hbase.BaseHandler):
    """Handle the /send URLs."""

    def __init__(self, application, request, **kwargs):
        super(SendHandler, self).__init__(application, request, **kwargs)

    @staticmethod
    def _valid_keys(method):
        return models.SEND_VALID_KEYS.get(method, None)

    # pylint: disable=too-many-locals
    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(202)
        json_obj = kwargs["json_obj"]
        j_get = json_obj.get

        # Mandatory keys
        job = j_get(models.JOB_KEY)
        kernel = j_get(models.KERNEL_KEY)
        branch = utils.clean_branch_name(j_get(models.GIT_BRANCH_KEY))

        # Optional keys
        report_type = j_get(models.REPORT_TYPE_KEY)
        countdown = j_get(models.DELAY_KEY)
        if countdown is None:
            countdown = self.settings["senddelay"]

        plans = j_get(models.PLANS_KEY)
        if plans is None:
            plans = []

        # Deprecated - ToDo: use report_type only in client code
        if j_get(models.SEND_BOOT_REPORT_KEY):
            report_type = 'boot'
        elif j_get(models.SEND_BUILD_REPORT_KEY):
            report_type = 'build'

        report_keys = REPORT_TYPE_KEYS.get(report_type)
        if not report_keys:
            response.status_code = 400
            response.reason = (
                "Invalid report type: {}.  Valid values are: {}"
                .format(report_type, ", ".join(REPORT_TYPE_KEYS.keys()))
            )
            return response
        report_data = {k: j_get(k) for k in report_keys}

        email_format = j_get(models.EMAIL_FORMAT_KEY, None)
        email_format, email_errors = _check_email_format(email_format)
        response.errors = email_errors
        schedule_errors = None

        try:
            countdown = int(countdown)
            if countdown < 0:
                countdown = abs(countdown)
                response.errrors = (
                    "Negative value specified for the '%s' key, "
                    "its positive value will be used instead (%ds)" %
                    (models.DELAY_KEY, countdown)
                )

            if countdown > MAX_DELAY:
                response.errors = (
                    "Delay value specified out of range (%ds), "
                    "maximum delay permitted (%ds) will be used instead" %
                    (countdown, MAX_DELAY)
                )
                countdown = MAX_DELAY

            when = (
                datetime.datetime.now(tz=bson.tz_util.utc) +
                datetime.timedelta(seconds=countdown))

            def j_get_list(key):
                value = j_get(key)
                if value is None:
                    value = []
                elif not isinstance(value, list):
                    value = [value]
                return value

            email_opts = {
                "to": j_get_list(models.REPORT_SEND_TO_KEY),
                "cc": j_get_list(models.REPORT_CC_KEY),
                "bcc": j_get_list(models.REPORT_BCC_KEY),
                "in_reply_to": j_get(models.IN_REPLY_TO_KEY),
                "subject": j_get(models.SUBJECT_KEY),
                "format": email_format,
            }

            self.log.info(
                TRIGGER_RECEIVED,
                self.request.remote_ip,
                job,
                branch,
                kernel,
                datetime.datetime.utcnow(),
                report_type
            )

            hashable_str = ''.join(str(x) for x in [
                job,
                branch,
                kernel,
                email_opts["to"],
                email_opts["cc"],
                email_opts["bcc"],
                email_opts["in_reply_to"],
                email_opts["subject"],
                report_type,
                str(email_format),
            ])
            schedule_hash = hashlib.sha1(hashable_str).hexdigest()

            try:
                lock_key = '-'.join([
                    'email', report_type, job, branch, kernel])

                with redis.lock.Lock(self.redisdb, lock_key, timeout=2):
                    if not self.redisdb.exists(schedule_hash):
                        self.redisdb.set(
                            schedule_hash, "schedule", ex=86400)

                        schedule_method = getattr(
                            self, "_schedule_{}_report".format(report_type))

                        errors, response.errors = schedule_method(
                            report_data, email_opts, countdown)

                        response.reason, response.status_code = \
                            _check_status(report_type, errors, when)
                    else:
                        self.log.warn(
                            TRIGGER_RECEIVED_ALREADY,
                            job, branch, kernel, report_type
                        )
                        taskq.send_multiple_emails_error.apply_async(
                            [
                                job,
                                branch,
                                kernel,
                                datetime.datetime.utcnow(),
                                email_format,
                                report_type,
                                email_opts
                            ]
                        )
                        response.status_code = 409
                        response.reason = ERR_409_MESSAGE
            except redis.lock.LockError:
                # Probably only reached during the unit tests.
                pass
        except (TypeError, ValueError):
            response.status_code = 400
            response.reason = (
                "Wrong value specified for 'delay': %s" % countdown)

        return response

    def _schedule_boot_report(self, report_data, email_opts, countdown):
        """Schedule the boot report performing some checks on the emails.

        :param report_data: Contents to use in the report.
        :type report_data: dict
        :param email_opts: The data necessary for scheduling a report.
        :type email_opts: dictionary
        :param countdown: Delay time before sending the email.
        :type countdown: int
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        job, git_branch, kernel, lab_name = (report_data[k] for k in [
            models.JOB_KEY,
            models.GIT_BRANCH_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
        ])

        if email_opts.get("to"):
            taskq.send_boot_report.apply_async(
                [
                    job,
                    git_branch,
                    kernel,
                    lab_name,
                    email_opts,
                ],
                countdown=countdown,
                link=taskq.trigger_bisections.s(
                    job,
                    git_branch,
                    kernel,
                    lab_name
                )
            )
        else:
            has_errors = True
            error_string = "No email addresses provided to send boot report to"
            self.log.error(
                "No email addresses to send boot report to for '%s-%s-%s'",
                job, git_branch, kernel)

        return has_errors, error_string

    def _schedule_build_report(self, report_data, email_opts, countdown):
        """Schedule the build report performing some checks on the emails.

        :param report_data: Contents to use in the report.
        :type report_data: dict
        :param email_opts: The data necessary for scheduling a report.
        :type email_opts: dictionary
        :param countdown: Delay time before sending the email.
        :type countdown: int
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        job, git_branch, kernel = (report_data[k] for k in [
            models.JOB_KEY,
            models.GIT_BRANCH_KEY,
            models.KERNEL_KEY,
        ])

        if email_opts.get("to"):
            taskq.send_build_report.apply_async(
                [
                    job,
                    git_branch,
                    kernel,
                    email_opts,
                ],
                countdown=countdown
            )
        else:
            has_errors = True
            error_string = (
                "No email addresses provided to send build report to")
            self.log.error(
                "No email addresses to send build report to for '%s-%s-%s'",
                job, git_branch, kernel)

        return has_errors, error_string

    def _schedule_bisect_report(self, report_data, email_opts, countdown):
        """Schedule the bisect report performing some checks on the emails.

        :param report_data: Contents to use in the report.
        :type report_data: dict
        :param email_opts: The data necessary for generating a report.
        :type email_opts: dictionary
        :param countdown: Delay time before sending the email.
        :type countdown: int
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        if email_opts.get("to"):
            taskq.send_bisect_report.apply_async(
                [
                    report_data,
                    email_opts,
                ],
                countdown=countdown
            )
        else:
            has_errors = True
            error_string = (
                "No email addresses provided to send bisection report to")
            self.log.error(error_string)

        return has_errors, error_string

    def _schedule_test_report(self, report_data, email_opts, countdown):
        """Schedule the test report performing some checks on the emails.

        :param report_data: Contents to use in the report.
        :type report_data: dict
        :param email_opts: The data necessary for scheduling a report.
        :type email_opts: dictionary
        :param countdown: Delay time before sending the email.
        :type countdown: int
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        job, git_branch, kernel, plans = (report_data[k] for k in [
            models.JOB_KEY,
            models.GIT_BRANCH_KEY,
            models.KERNEL_KEY,
            models.PLANS_KEY
        ])

        if email_opts.get("to"):
            taskq.send_test_report.apply_async(
                [
                    job,
                    git_branch,
                    kernel,
                    plans,
                    report_data,
                    email_opts,
                ],
                countdown=countdown
            )
        else:
            has_errors = True
            error_string = "No email addresses provided to send test report to"
            self.log.error(
                "%s for '%s-%s-%s-plans_%s'",
                error_string, job, git_branch, kernel, "_".join(plans))

        return has_errors, error_string

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None
        valid_token, _ = self.validate_req_token("DELETE")

        if valid_token:
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def execute_get(self, *args, **kwargs):
        """Execute the GET pre-operations.

        Checks that everything is OK to perform a GET.
        """
        response = None
        valid_token, _ = self.validate_req_token("GET")

        if valid_token:
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)

        return response


def _check_status(report_type, errors, when):
    """Check the status of the boot/build report schedule.

    :param report_type: Report type.
    :type send_boot: str
    :param errors_errors: If there have been errors in scheduling the report.
    :type boot_errors: bool
    :param when: A datetime object when the report should have been scheduled.
    :type when: datetime.datetime
    :return A tuple with the reason message and the status code.
    """

    if errors:
        reason = "No {} email reports scheduled to be sent".format(
            report_type)
        status_code = 400
    else:
        reason = "{} email report scheduled to be sent at '{}' UTC".format(
            report_type, when.isoformat())
        status_code = 202

    return reason, status_code


def _check_email_format(email_format):
    """Check that the specified email formats are valid.

    :param email_format: The email formats to validate.
    :type email_format: list
    :return The valid email format as list, and a list of errors.
    """
    errors = []
    valid_format = []

    if email_format:
        if not isinstance(email_format, types.ListType):
            email_format = [email_format]

        format_copy = copy.copy(email_format)
        for e_format in format_copy:
            if e_format in models.VALID_EMAIL_FORMATS:
                valid_format.append(e_format)
            else:
                email_format.remove(e_format)
                errors.append(
                    "Invalid email format '%s' specified, "
                    "will be ignored" % e_format)

        # Did we remove everything?
        if not email_format:
            valid_format.append(models.EMAIL_TXT_FORMAT_KEY)
            errors.append(
                "No valid email formats specified, defaulting to '%s'" %
                models.EMAIL_TXT_FORMAT_KEY)
    else:
        # By default, do not add warnings.
        valid_format.append(models.EMAIL_TXT_FORMAT_KEY)

    return valid_format, errors
