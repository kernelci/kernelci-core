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

import models
import utils
import utils.db
import utils.report.common as rcommon

TEST_REPORT_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_INSTANCE_KEY,
    models.BOARD_KEY,
    models.BOOT_ID_KEY,
    models.BOOT_LOG_HTML_KEY,
    models.BOOT_LOG_KEY,
    models.BUILD_ID_KEY,
    models.BUILD_ENVIRONMENT_KEY,
    models.COMPILER_VERSION_FULL_KEY,
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
    models.INITRD_KEY,
    models.INITRD_INFO_KEY,
    models.JOB_ID_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
    models.LAB_NAME_KEY,
    models.METADATA_KEY,
    models.NAME_KEY,
    models.STATUS_KEY,
    models.TEST_CASES_KEY,
    models.SUB_GROUPS_KEY,
    models.TIME_KEY,
    models.VCS_COMMIT_KEY,
    models.VERSION_KEY,
]

# FIXME: get this from test-configs.yaml
TEST_PLAN_OPTIONS = {
    "v4l2-compliance-uvc": {
        "subject": "v4l2-compliance on uvcvideo",
        "template": "plans/v4l2-compliance.txt",
        "params": {
            "driver_name": "uvcvideo",
        },
    },
    "v4l2-compliance-vivid": {
        "subject": "v4l2-compliance on vivid",
        "template": "plans/v4l2-compliance.txt",
        "params": {
            "driver_name": "vivid",
        },
    },
}


def _regression_message(data):
    last_pass = data[0]
    first_fail = data[1]
    last_fail = data[-1]

    if len(data) == 2:
        return "new failure (last pass: {})".format(
            last_pass[models.KERNEL_KEY])

    delta = last_fail[models.CREATED_KEY] - first_fail[models.CREATED_KEY]
    plural = 's' if delta.days > 1 else ''
    return "failing since {} day{} (last pass: {}, first fail: {})".format(
        delta.days, plural, last_pass[models.KERNEL_KEY],
        first_fail[models.KERNEL_KEY])


def _add_test_group_data(group, db, spec, hierarchy=[]):
    hierarchy = hierarchy + [group[models.NAME_KEY]]
    case_collection = db[models.TEST_CASE_COLLECTION]
    regr_collection = db[models.TEST_REGRESSION_COLLECTION]
    group_collection = db[models.TEST_GROUP_COLLECTION]
    regr_spec = dict(spec)
    regr_count = 0

    test_cases = []
    for test_case_id in group[models.TEST_CASES_KEY]:
        test_case = utils.db.find_one2(case_collection, test_case_id)
        if test_case[models.STATUS_KEY] == "FAIL":
            regr_spec[models.HIERARCHY_KEY] = (
                hierarchy + [test_case[models.NAME_KEY]])
            regr = utils.db.find_one2(regr_collection, regr_spec)
            test_case["failure_message"] = (
                _regression_message(regr[models.REGRESSIONS_KEY])
                if regr else "never passed")
            if regr:
                regr_count += 1
        test_cases.append(test_case)

    test_cases.sort(key=lambda tc: tc[models.INDEX_KEY])

    sub_groups = []
    for sub_group_id in group[models.SUB_GROUPS_KEY]:
        sub_group = utils.db.find_one2(group_collection, sub_group_id)
        _add_test_group_data(sub_group, db, spec, hierarchy)
        sub_groups.append(sub_group)

    total = {status: 0 for status in ["PASS", "FAIL", "SKIP"]}

    for test_case in test_cases:
        total[test_case[models.STATUS_KEY]] += 1

    for sub_group_total in (sg["total"] for sg in sub_groups):
        for status, count in sub_group_total.iteritems():
            total[status] += count

    regr_count += sum(sg["regressions"] for sg in sub_groups)

    group.update({
        "test_cases": test_cases,
        "sub_groups": sub_groups,
        "regressions": regr_count,
        "total_tests": sum(total.values()),
        "total": total,
    })


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
    :return A tuple with the email body, the email subject and the headers as
    dictionary.  If an error occured, None.
    """
    database = utils.db.get_db_connection(db_options)

    job, branch, kernel, plan = (data[k] for k in [
        models.JOB_KEY,
        models.GIT_BRANCH_KEY,
        models.KERNEL_KEY,
        models.PLAN_KEY,
    ])

    plan_options = TEST_PLAN_OPTIONS.get(plan, {})

    spec = {x: y for x, y in data.iteritems() if x != models.PLAN_KEY}
    group_spec = dict(spec)
    group_spec.update({
        models.NAME_KEY: plan,
        models.PARENT_ID_KEY: None,
    })

    groups = list(utils.db.find(
        database[models.TEST_GROUP_COLLECTION],
        spec=group_spec,
        fields=TEST_REPORT_FIELDS))

    if not groups:
        utils.LOG.warning("Failed to find test group documents")
        return None

    for group in groups:
        group_spec = dict(spec)
        group_spec.update({
            k: group[k] for k in [
                models.DEVICE_TYPE_KEY,
                models.ARCHITECTURE_KEY,
                models.BUILD_ENVIRONMENT_KEY,
                models.DEFCONFIG_FULL_KEY,
            ]
        })
        _add_test_group_data(group, database, group_spec)

    tests_total = sum(group["total_tests"] for group in groups)
    regr_total = sum(group["regressions"] for group in groups)

    plan_subject = plan_options.get("subject", plan)
    subject_str = "{}/{} {}: {} tests, {} regressions ({})".format(
        job, branch, plan_subject, tests_total, regr_total, kernel)

    git_url, git_commit = (groups[0][k] for k in [
        models.GIT_URL_KEY, models.GIT_COMMIT_KEY])

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
        "plan": plan,
        "boot_log": models.BOOT_LOG_KEY,
        "boot_log_html": models.BOOT_LOG_HTML_KEY,
        "storage_url": rcommon.DEFAULT_STORAGE_URL,
        "test_groups": groups,
    }

    template = plan_options.get("template", "test.txt")
    template_data.update(plan_options.get("params", {}))
    body = rcommon.create_txt_email(template, **template_data)

    return body, subject_str, headers
