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

"""Create the tests email report."""

import json
import os

import models
import utils
import utils.db
import utils.report.common as rcommon

TEST_REPORT_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_INSTANCE_KEY,
    models.BOARD_KEY,
    models.BOOT_ID_KEY,
    models.BUILD_ID_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_KEY,
    models.DEFINITION_URI_KEY,
    models.DEVICE_TYPE_KEY,
    models.GIT_BRANCH_KEY,
    models.GIT_COMMIT_KEY,
    models.GIT_DESCRIBE_KEY,
    models.GIT_URL_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.LAB_NAME_KEY,
    models.METADATA_KEY,
    models.NAME_KEY,
    models.STATUS_KEY,
    models.TEST_CASE_KEY,
    models.TIME_KEY,
    models.VCS_COMMIT_KEY,
    models.VERSION_KEY,
]


def create_test_report(data, email_format, db_options,
                       base_path=utils.BASE_PATH):
    """Create the tests report email to be sent.

    :param data: The meta-data for the test job.
    :type data: dictionary
    :param email_format: The email format to send.
    :type email_format: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param base_path: Path to the top-level storage directory.
    :type base_path: string
    :return A tuple with the TXT email body, the HTML email body and the
    headers as dictionary.  If an error occured, None.
    """
    database = utils.db.get_db_connection(db_options)

    job, branch, kernel = (data[k] for k in [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
    ])

    specs = {x: data[x] for x in data.keys() if data[x]}

    test_groups = utils.db.find(
        database[models.TEST_GROUP_COLLECTION],
        100,
        0,
        spec=specs,
        fields=TEST_REPORT_FIELDS)

    if not test_groups:
        utils.LOG.warning("Failed to find test group document")
        return None

    test_groups = [d for d in test_groups.clone()]

    for tg in test_groups:
        # tg is a dictionary, where we need to add a new field test_case_list
        # test_case_list is a list of dictionary with every test case
        testcase = tg['test_case']
        tg['test_case_list'] = []
        for tc in testcase:
            # tc is a _id from the testcase
            test_case_doc = utils.db.find_one2(
               database[models.TEST_CASE_COLLECTION],
               {"_id": tc})
            tg['test_case_list'].append(test_case_doc)

        resultlist = [test['status'] for test in tg['test_case_list']]
        tg['total_tests'] = len(resultlist)
        tg['total_pass'] = len([e for e in resultlist if e == "PASS"])
        tg['total_fail'] = len([e for e in resultlist if e == "FAIL"])
        tg['total_skip'] = len([e for e in resultlist if e == "SKIP"])

    # Remove the entries named "lava" since they don't contain any result
    # from the defined test plans
    for item in list(test_groups):
        if item['name'] == 'lava':
            test_groups.remove(item)

    subject_str = "Test results for {}/{} - {}".format(
        job, branch, kernel)

    git_url = test_groups[0][models.GIT_URL_KEY]
    git_commit = test_groups[0][models.GIT_COMMIT_KEY]

    headers = {
        rcommon.X_REPORT: rcommon.TEST_REPORT_TYPE,
        rcommon.X_BRANCH: branch,
        rcommon.X_TREE: job,
        rcommon.X_KERNEL: kernel,
    }

    template_data = {
        "subject_str": subject_str,
        "tree": job,
        "branch": branch,
        "git_url": git_url,
        "kernel": kernel,
        "git_commit": git_commit,
        "test_groups": test_groups,
    }

    if models.EMAIL_TXT_FORMAT_KEY in email_format:
        txt_body = rcommon.create_txt_email("test.txt", **template_data)
    else:
        txt_body = None

    if models.EMAIL_HTML_FORMAT_KEY in email_format:
        html_body = rcommon.create_html_email("test.html", **template_data)
    else:
        html_body = None

    return txt_body, html_body, subject_str, headers
