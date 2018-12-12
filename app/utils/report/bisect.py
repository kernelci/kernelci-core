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

"""Create the bisect email report."""

import json
import os

import models
import utils
import utils.db
import utils.report.common as rcommon


def create_bisect_report(data, email_options, db_options,
                         base_path=utils.BASE_PATH):
    """Create the bisection report email to be sent.

    :param data: The meta-data for the bisection job.
    :type data: dictionary
    :param email_options: The email options.
    :type email_options: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param base_path: Path to the top-level storage directory.
    :type base_path: string
    :return A tuple with the TXT email body, the HTML email body and the
    headers as dictionary.  If an error occured, None.
    """
    database = utils.db.get_db_connection(db_options)

    job, branch, kernel, test_suite, lab, target = (data[k] for k in [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
        models.TYPE_KEY,
        models.LAB_NAME_KEY,
        models.DEVICE_TYPE_KEY,
    ])

    email_format, email_subject = (email_options[k] for k in [
        "format", "subject",
    ])

    specs = {x: data[x] for x in [
        models.TYPE_KEY,
        models.ARCHITECTURE_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.LAB_NAME_KEY,
        models.DEVICE_TYPE_KEY,
        models.BISECT_GOOD_COMMIT_KEY,
        models.BISECT_BAD_COMMIT_KEY,
    ]}
    doc = utils.db.find_one2(database[models.BISECT_COLLECTION], specs)
    if not doc:
        utils.LOG.warning("Failed to find bisection document")
        return None

    headers = {
        rcommon.X_REPORT: rcommon.BISECT_REPORT_TYPE,
        rcommon.X_BRANCH: branch,
        rcommon.X_TREE: job,
        rcommon.X_KERNEL: kernel,
        rcommon.X_LAB: lab,
    }

    log_path_elements = (base_path, job, branch, kernel) + tuple(
        data[k] for k in [
            models.ARCHITECTURE_KEY,
            models.DEFCONFIG_FULL_KEY,
            models.LAB_NAME_KEY,
            models.BISECT_LOG_KEY,
        ]
    )
    log_path = os.path.join(*log_path_elements)
    with open(log_path) as log_file:
        log_data = json.load(log_file)

    url_params = {
        'boot_url': rcommon.DEFAULT_BOOT_URL,
        'job': job,
        'git_branch': branch,
    }
    boot_data = {b['status']: b['git_describe']
                 for b in doc[models.BISECT_DATA_KEY]}
    good_url, bad_url = (
        rcommon.BOOT_SUMMARY_URL.format(kernel=boot_data[x], **url_params)
        for x in ['PASS', 'FAIL'])

    template_data = {
        "subject_str": email_subject,
        "good": doc[models.BISECT_GOOD_SUMMARY_KEY],
        "bad": doc[models.BISECT_BAD_SUMMARY_KEY],
        "good_details_url": good_url,
        "bad_details_url": bad_url,
        "good_describe": boot_data['PASS'],
        "bad_describe": boot_data['FAIL'],
        "found": doc[models.BISECT_FOUND_SUMMARY_KEY],
        "checks": doc[models.BISECT_CHECKS_KEY],
        "tree": job,
        "git_url": doc[models.GIT_URL_KEY],
        "branch": branch,
        "target": doc[models.DEVICE_TYPE_KEY],
        "arch": doc[models.ARCHITECTURE_KEY],
        "lab_name": lab,
        "defconfig": doc[models.DEFCONFIG_FULL_KEY],
        "test_suite": test_suite,
        "show": log_data["show"],
        "log": log_data["log"],
    }

    if models.EMAIL_TXT_FORMAT_KEY in email_format:
        txt_body = rcommon.create_txt_email("bisect.txt", **template_data)
    else:
        txt_body = None

    if models.EMAIL_HTML_FORMAT_KEY in email_format:
        html_body = rcommon.create_html_email("bisect.html", **template_data)
    else:
        html_body = None

    return txt_body, html_body, headers
