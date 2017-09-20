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
        job = j_get(models.JOB_KEY)
        kernel = j_get(models.KERNEL_KEY)
        branch = utils.clean_branch_name(j_get(models.GIT_BRANCH_KEY))
        lab_name = j_get(models.LAB_NAME_KEY, None)

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

            if send_boot or send_build:
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
                    "boot_cc_emails":
                        j_get(models.BOOT_REPORT_SEND_CC_KEY, None),
                    "boot_bcc_emails":
                        j_get(models.BOOT_REPORT_SEND_BCC_KEY, None),
                    "build_emails": j_get(
                        models.BUILD_REPORT_SEND_TO_KEY, None),
                    "build_cc_emails":
                        j_get(models.BUILD_REPORT_SEND_CC_KEY, None),
                    "build_bcc_emails":
                        j_get(models.BUILD_REPORT_SEND_BCC_KEY, None),
                    "generic_emails": j_get(models.REPORT_SEND_TO_KEY, None),
                    "generic_cc_emails": j_get(models.REPORT_CC_KEY, None),
                    "generic_bcc_emails": j_get(models.REPORT_BCC_KEY, None),
                    "in_reply_to": j_get(models.IN_REPLY_TO_KEY, None),
                    "subject": j_get(models.SUBJECT_KEY, None),
                    "db_options": self.settings["dboptions"],
                }

                email_type = []
                if send_boot:
                    email_type.append("boot")

                if send_build:
                    email_type.append("build")

                self.log.info(
                    TRIGGER_RECEIVED,
                    self.request.remote_ip,
                    job,
                    branch,
                    kernel,
                    datetime.datetime.utcnow(),
                    str(email_type)
                )

                hashable_str = "{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}".format(
                    job,
                    branch,
                    kernel,
                    str(schedule_data["boot_emails"]),
                    str(schedule_data["boot_cc_emails"]),
                    str(schedule_data["boot_bcc_emails"]),
                    str(schedule_data["build_emails"]),
                    str(schedule_data["build_cc_emails"]),
                    str(schedule_data["build_bcc_emails"]),
                    str(schedule_data["generic_emails"]),
                    str(schedule_data["generic_cc_emails"]),
                    str(schedule_data["generic_bcc_emails"]),
                    schedule_data["in_reply_to"],
                    schedule_data["subject"],
                    str(email_type),
                    str(email_format)
                )
                schedule_hash = hashlib.sha1(hashable_str).hexdigest()

                try:
                    lock_key = \
                        "email-{}-{}-{}-{}".format(
                            str(email_type), job, branch, kernel)

                    with redis.lock.Lock(self.redisdb, lock_key, timeout=2):
                        if not self.redisdb.exists(schedule_hash):
                            self.redisdb.set(
                                schedule_hash, "schedule", ex=86400)

                            if send_boot:
                                email_type.append("boot")
                                boot_errors, response.errors = \
                                    self._schedule_boot_report(
                                        job,
                                        branch,
                                        kernel,
                                        lab_name, email_format, schedule_data)

                            if send_build:
                                build_errors, response.errors = \
                                    self._schedule_build_report(
                                        job,
                                        branch,
                                        kernel, email_format, schedule_data)

                            response.reason, response.status_code = \
                                _check_status(
                                    send_boot,
                                    send_build,
                                    boot_errors, build_errors, when)
                        else:
                            self.log.warn(
                                TRIGGER_RECEIVED_ALREADY,
                                job, branch, kernel, str(email_type)
                            )
                            taskq.send_multiple_emails_error.apply_async(
                                [
                                    job,
                                    branch,
                                    kernel,
                                    datetime.datetime.utcnow(),
                                    email_format,
                                    email_type,
                                    schedule_data
                                ]
                            )
                            response.status_code = 409
                            response.reason = ERR_409_MESSAGE
                except redis.lock.LockError:
                    # Probably only reached during the unit tests.
                    pass
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
    def _schedule_boot_report(
            self,
            job, git_branch, kernel, lab_name, email_format, schedule_data):
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
        s_get = schedule_data.get

        to_addrs, cc_addrs, bcc_addrs = _get_email_addresses(
            s_get("boot_emails"),
            s_get("generic_emails"),
            cc=s_get("boot_cc_emails"),
            bcc=s_get("boot_bcc_emails"),
            g_cc=s_get("generic_cc_emails"),
            g_bcc=s_get("generic_bcc_emails")
        )

        if to_addrs:
            taskq.send_boot_report.apply_async(
                [
                    job,
                    git_branch,
                    kernel,
                    lab_name,
                    email_format,
                    to_addrs,
                    s_get("db_options"),
                    cc_addrs,
                    bcc_addrs,
                    s_get("in_reply_to"),
                    s_get("subject")
                ],
                link=taskq.trigger_bisections.s(
                    job,
                    git_branch,
                    kernel,
                    lab_name,
                    s_get("db_options")
                ),
                countdown=s_get("countdown")
            )
        else:
            has_errors = True
            error_string = "No email addresses provided to send boot report to"
            self.log.error(
                "No email addresses to send boot report to for '%s-%s-%s'",
                job, git_branch, kernel)

        return has_errors, error_string

    def _schedule_build_report(
            self, job, git_branch, kernel, email_format, schedule_data):
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
        s_get = schedule_data.get

        to_addrs, cc_addrs, bcc_addrs = _get_email_addresses(
            s_get("build_emails"),
            s_get("generic_emails"),
            cc=s_get("build_cc_emails"),
            bcc=s_get("build_bcc_emails"),
            g_cc=s_get("generic_cc_emails"),
            g_bcc=s_get("generic_bcc_emails")
        )

        if to_addrs:
            taskq.send_build_report.apply_async(
                [
                    job,
                    git_branch,
                    kernel,
                    email_format,
                    to_addrs,
                    s_get("db_options")
                ],
                kwargs={
                    "cc_addrs": cc_addrs,
                    "bcc_addrs": bcc_addrs,
                    "in_reply_to": s_get("in_reply_to"),
                    "subject": s_get("subject")
                },
                countdown=s_get("countdown")
            )
        else:
            has_errors = True
            error_string = (
                "No email addresses provided to send build report to")
            self.log.error(
                "No email addresses to send build report to for '%s-%s-%s'",
                job, git_branch, kernel)

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

    if send_boot and send_build and boot_errors and build_errors:
        reason = "No email reports scheduled to be sent"
        status_code = 400
    elif send_boot and send_build and boot_errors and not build_errors:
        reason = (
            "Build email report scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif send_boot and send_build and not boot_errors and build_errors:
        reason = (
            "Boot email report scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif send_boot and send_build and not boot_errors and not build_errors:
        reason = (
            "Email reports scheduled to be sent at '%s' UTC" %
            when.isoformat())
    elif not send_boot and send_build and not boot_errors and build_errors:
        reason = (
            "Build email report not scheduled to be sent")
        status_code = 400
    elif not send_boot and send_build and not boot_errors and not build_errors:
        reason = (
            "Build email report scheduled to be sent at '%s' UTC" %
            when)
    elif send_boot and not send_build and boot_errors and not build_errors:
        reason = (
            "Boot email report not scheduled to be sent")
        status_code = 400
    elif send_boot and not send_build and not boot_errors and not build_errors:
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


def _get_email_addresses(
        report_emails,
        generic_emails,
        cc=None,
        bcc=None,
        g_cc=None,
        g_bcc=None):
    """Create to, cc and bcc email addresses lists.

    :param report_emails: The emails to analyze.
    :type report_emails: string or list
    :param generic_emails: The generic emails to analyze.
    :type generic_emails: string or list
    :param cc: The CC emails to analyze.
    :type cc: string or list
    :param bcc: The BCC emails to analyze.
    :type bcc: string or list
    :param g_cc: The generic CC emails to analyze.
    :type g_cc: string or list
    :param g_bcc: The generic BCC emails to analyze.
    :type g_bcc: string or list
    :return A 3-tuple with: list of TO, CC and BCC email addresses or empty
    lists.
    """
    to_addrs = []
    cc_addrs = []
    bcc_addrs = []

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

    if cc:
        if isinstance(cc, types.ListType):
            cc_addrs.extend(cc)
        elif isinstance(cc, types.StringTypes):
            cc_addrs.append(cc)

    if g_cc:
        if isinstance(g_cc, types.ListType):
            cc_addrs.extend(g_cc)
        elif isinstance(g_cc, types.StringTypes):
            cc_addrs.append(g_cc)

    if bcc:
        if isinstance(bcc, types.ListType):
            bcc_addrs.extend(bcc)
        elif isinstance(bcc, types.StringTypes):
            bcc_addrs.append(bcc)

    if g_bcc:
        if isinstance(g_bcc, types.ListType):
            bcc_addrs.extend(g_bcc)
        elif isinstance(g_bcc, types.StringTypes):
            bcc_addrs.append(g_bcc)

    return to_addrs, cc_addrs, bcc_addrs
