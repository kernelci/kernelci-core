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

"""This module is used to send boot and build report email."""

import bson
import copy
import datetime
import types

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import taskqueue.tasks as taskq

# Max delay in sending email report set to 5hrs.
MAX_DELAY = 18000


# pylint: disable=too-many-public-methods
class SendHandler(hbase.BaseHandler):
    """Handle the /send URLs."""

    def __init__(self, application, request, **kwargs):
        super(SendHandler, self).__init__(application, request, **kwargs)

    @staticmethod
    def _valid_keys(method):
        return hcommon.SEND_VALID_KEYS.get(method, None)

    # pylint: disable=too-many-locals
    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(202)

        json_obj = kwargs["json_obj"]

        j_get = json_obj.get
        job = j_get(models.JOB_KEY)
        kernel = j_get(models.KERNEL_KEY)
        lab_name = j_get(models.LAB_NAME_KEY, None)

        self.log.info(
            "Email trigger received from IP '%s' for '%s-%s' at %s",
            self.request.remote_ip,
            job,
            kernel,
            datetime.datetime.utcnow()
        )

        countdown = j_get(models.DELAY_KEY, self.settings["senddelay"])
        if countdown is None:
            countdown = self.settings["senddelay"]

        try:
            send_boot = bool(j_get(models.SEND_BOOT_REPORT_KEY, False))
            send_build = bool(j_get(models.SEND_BUILD_REPORT_KEY, False))

            email_format = j_get(models.EMAIL_FORMAT_KEY, None)
            email_format, email_errors = _check_email_format(email_format)
            response.errors = email_errors

            boot_errors = False
            build_errors = False

            if any([send_boot, send_build]):
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

                schedule_data = {
                    "countdown": countdown,
                    "boot_emails": j_get(models.BOOT_REPORT_SEND_TO_KEY, None),
                    "build_emails": j_get(
                        models.BUILD_REPORT_SEND_TO_KEY, None),
                    "generic_emails": j_get(models.REPORT_SEND_TO_KEY, None),
                    "db_options": self.settings["dboptions"],
                    "mail_options": self.settings["mailoptions"]
                }

                if send_boot:
                    boot_errors, response.errors = self._schedule_boot_report(
                        job, kernel, lab_name, email_format, schedule_data)

                if send_build:
                    build_errors, response.errors = \
                        self._schedule_build_report(
                            job, kernel, email_format, schedule_data)

                response.reason, response.status_code = _check_status(
                    send_boot, send_build, boot_errors, build_errors, when)
            else:
                response.status_code = 400
                response.reason = (
                    "Don't know which report to send: either specify "
                    " '%s' or '%s'" %
                    (models.SEND_BOOT_REPORT_KEY, models.SEND_BUILD_REPORT_KEY)
                )
        except (TypeError, ValueError):
            response.status_code = 400
            response.reason = (
                "Wrong value specified for 'delay': %s" % countdown)

        return response

    # pylint: disable=too-many-arguments
    def _schedule_boot_report(self,
                              job,
                              kernel, lab_name, email_format, schedule_data):
        """Schedule the boot report performing some checks on the emails.

        :param job: The name of the job.
        :type job: string
        :param kernel: The name of the kernel.
        :type kernel: string
        :param lab_name: The name of the lab.
        :type lab_name: string
        :param email_format: The email format to send.
        :type email_format: list
        :param schedule_data: The data necessary for scheduling a report.
        :type schedule_data: dictionary
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        to_addrs = _get_email_addresses(
            schedule_data["boot_emails"], schedule_data["generic_emails"])

        if to_addrs:
            taskq.send_boot_report.apply_async(
                [
                    job,
                    kernel,
                    lab_name,
                    email_format,
                    to_addrs,
                    schedule_data["db_options"],
                    schedule_data["mail_options"]
                ],
                countdown=schedule_data["countdown"]
            )
        else:
            has_errors = True
            error_string = "No email addresses provided to send boot report to"
            self.log.error(
                "No email addresses to send boot report to for '%s-%s'",
                job, kernel)

        return has_errors, error_string

    def _schedule_build_report(self, job, kernel, email_format, schedule_data):
        """Schedule the build report performing some checks on the emails.

        :param job: The name of the job.
        :type job: string
        :param kernel: The name of the kernel.
        :type kernel: string
        :param email_format: The email format to send.
        :type email_format: list
        :param schedule_data: The data necessary for scheduling a report.
        :type schedule_data: dictionary
        :return A tuple with as first parameter a bool indicating if the
        scheduling had success, as second argument the error string in case
        of error or None.
        """
        has_errors = False
        error_string = None

        to_addrs = _get_email_addresses(
            schedule_data["build_emails"], schedule_data["generic_emails"])

        if to_addrs:
            taskq.send_build_report.apply_async(
                [
                    job,
                    kernel,
                    email_format,
                    to_addrs,
                    schedule_data["db_options"],
                    schedule_data["mail_options"]
                ],
                countdown=schedule_data["countdown"]
            )
        else:
            has_errors = True
            error_string = (
                "No email addresses provided to send build report to")
            self.log.error(
                "No email addresses to send build report to for '%s-%s'",
                job, kernel)

        return has_errors, error_string

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None
        valid_token, _ = self.validate_req_token("DELETE")

        if valid_token:
            response = hresponse.HandlerResponse(501)
            response.reason = hcommon.METHOD_NOT_IMPLEMENTED
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def execute_get(self, *args, **kwargs):
        """Execute the GET pre-operations.

        Checks that everything is OK to perform a GET.
        """
        response = None
        valid_token, _ = self.validate_req_token("GET")

        if valid_token:
            response = hresponse.HandlerResponse(501)
            response.reason = hcommon.METHOD_NOT_IMPLEMENTED
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response


def _check_status(send_boot, send_build, boot_errors, build_errors, when):
    """Check the status of the boot/build report schedule.

    :param send_boot: If a boot report should have been sent.
    :type send_boot: bool
    :param send_build: If a build report should have been sent.
    :type send_build: bool
    :param boot_errors: If there have been errors in scheduling the boot
    report.
    :type boot_errors: bool
    :param build_errors: If there have been errors in scheduling the build
    report.
    :type build_errors: bool
    :param when: A datetime object when the report should have been scheduled.
    :type when: datetime.datetime
    :return A tuple with the reason message and the status code.
    """
    status_code = 202
    reason = None

    if all([send_boot, send_build, boot_errors, build_errors]):
        reason = "No email reports scheduled to be sent"
        status_code = 400
    elif all([
            send_boot, send_build, boot_errors, not build_errors]):
        reason = (
            "Build email report scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif all([
            send_boot, send_build, not boot_errors, build_errors]):
        reason = (
            "Boot email report scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif all([
            send_boot,
            send_build, not boot_errors, not build_errors]):
        reason = (
            "Email reports scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif all([
            not send_boot,
            send_build, not boot_errors, build_errors]):
        reason = (
            "Build email report not scheduled to be sent")
        status_code = 400
    elif all([
            not send_boot,
            send_build, not boot_errors, not build_errors]):
        reason = (
            "Build email report scheduled to be sent at '%s' UTC" %
            when)
    elif all([
            send_boot,
            not send_build, boot_errors, not build_errors]):
        reason = (
            "Boot email report not scheduled to be sent")
        status_code = 400
    elif all([
            send_boot,
            not send_build, not boot_errors, not build_errors]):
        reason = (
            "Boot email report scheduled to be sent at '%s' UTC" %
            when)

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


def _get_email_addresses(report_emails, generic_emails):
    """Return a list of email address from the ones provided.

    :param report_emails: The emails to analyze.
    :type report_emails: string or list
    :param generic_emails: The generic emails to analyze.
    :type generic_emails: string or list
    :return A list of email addresses or an empty list.
    """
    to_addrs = []

    if report_emails:
        if isinstance(report_emails, types.ListType):
            to_addrs.extend(report_emails)
        elif isinstance(report_emails, types.StringTypes):
            to_addrs.append(report_emails)

    if generic_emails:
        if isinstance(generic_emails, types.ListType):
            to_addrs.extend(generic_emails)
        elif isinstance(generic_emails, types.StringTypes):
            to_addrs.append(generic_emails)

    return to_addrs
