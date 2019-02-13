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

import hashlib
import json
import redis
import os

import models
import utils
import utils.db
import utils.database.redisdb as redisdb
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
    :return A tuple with the TXT email body and the headers as dictionary.  If
    an error occured, None.
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
        models.BUILD_ENVIRONMENT_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
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

    report_hashable_str = "-".join(str(x) for x in [
        doc[models.BISECT_FOUND_SUMMARY_KEY],
        doc[models.KERNEL_KEY],
        email_options["to"],
        email_options["cc"],
    ])
    report_hash = hashlib.sha1(report_hashable_str).hexdigest()
    redisdb_conn = redisdb.get_db_connection(db_options)
    if redisdb_conn.exists(report_hash):
        utils.LOG.info("Bisection report already sent for {}: {}".format(
            doc[models.KERNEL_KEY],
            doc[models.BISECT_FOUND_SUMMARY_KEY]))
        return None
    redisdb_conn.set(report_hash, "bisection-report", ex=86400)

    headers = {
        rcommon.X_REPORT: rcommon.BISECT_REPORT_TYPE,
        rcommon.X_BRANCH: branch,
        rcommon.X_TREE: job,
        rcommon.X_KERNEL: kernel,
        rcommon.X_LAB: lab,
    }

    rel_path = '/'.join((job, branch, kernel) + tuple(
        data[k] for k in [
            models.ARCHITECTURE_KEY,
            models.DEFCONFIG_FULL_KEY,
            models.BUILD_ENVIRONMENT_KEY,
            models.LAB_NAME_KEY,
        ]
    ))

    log_path = os.path.join(base_path, rel_path, data[models.BISECT_LOG_KEY])
    with open(log_path) as log_file:
        log_data = json.load(log_file)

    url_params = {
        'boot_url': rcommon.DEFAULT_BOOT_URL,
        'job': job,
        'git_branch': branch,
    }

    boot_data = {b["status"]: b for b in doc[models.BISECT_DATA_KEY]}
    bad_describe = boot_data["FAIL"]["git_describe"]
    bad_details_url = '/'.join([
        rcommon.DEFAULT_BASE_URL, "boot", "id", str(boot_data["FAIL"]["_id"])])
    log_url_txt, log_url_html = ('/'.join([
        rcommon.DEFAULT_STORAGE_URL, rel_path, boot_data["FAIL"][k]])
        for k in [models.BOOT_LOG_KEY, models.BOOT_LOG_HTML_KEY])

    cc = doc[models.COMPILER_KEY]
    cc_ver = doc[models.COMPILER_VERSION_KEY]
    compiler_str = "-".join([cc, cc_ver]) if cc_ver else cc

    template_data = {
        "subject_str": email_subject,
        "bad": doc[models.BISECT_BAD_SUMMARY_KEY],
        "bad_details_url": bad_details_url,
        "bad_describe": bad_describe,
        "log_url_txt": log_url_txt,
        "log_url_html": log_url_html,
        "found": doc[models.BISECT_FOUND_SUMMARY_KEY],
        "checks": doc[models.BISECT_CHECKS_KEY],
        "tree": job,
        "git_url": doc[models.GIT_URL_KEY],
        "branch": branch,
        "target": doc[models.DEVICE_TYPE_KEY],
        "arch": doc[models.ARCHITECTURE_KEY],
        "lab_name": lab,
        "defconfig": doc[models.DEFCONFIG_FULL_KEY],
        "compiler": compiler_str,
        "test_suite": test_suite,
        "show": log_data["show"],
        "log": log_data["log"],
    }

    body = rcommon.create_txt_email("bisect.txt", **template_data)

    return body, headers
