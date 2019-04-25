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

"""Create the boot email report."""

import copy
import itertools
import jenkins
import pymongo
import random

import models
import utils.db
import utils.report.common as rcommon
import utils.bisect.boot as bbisect

# Register normal Unicode gettext.
G_ = rcommon.L10N.ugettext
# Register plural forms Unicode gettext.
P_ = rcommon.L10N.ungettext


BOOT_SEARCH_SORT = [
    (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
    (models.BOARD_KEY, pymongo.ASCENDING)
]

BOOT_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.BUILD_ENVIRONMENT_KEY,
    models.LAB_NAME_KEY,
    models.MACH_KEY,
    models.STATUS_KEY
]

HREF_STYLE = u"style=\"color: black; text-decoration: none\""

# Regressions strings.
SINGULAR_FAILURE_HTML = \
    u"<a href=\"{boot_regressions_url:s}\" " + HREF_STYLE + u">" + \
    u"failing since <span style=\"color: {red:s}\">{days:d} day</span></a>"
PLURAL_FAILURE_HTML = \
    u"<a href=\"{boot_regressions_url:s}\" " + HREF_STYLE + u">" + \
    u"failing since <span style=\"color: {red:s}\">{days:d} days</span></a>"

SINGULAR_FAILURE_TXT = u"failing since {days:d} day"
PLURAL_FAILURE_TXT = u"failing since {days:d} days"

BOOT_ID_HTML = u"<a href=\"{boot_id_url:s}\">{lab_name:s}</a>"
NEW_FAIL_HTML = u"<span style=\"color: {red:s}\">" + \
    u"<a href=\"{boot_regressions_url:s}\" " + HREF_STYLE + u">" + \
    u"new failure</a></span>"
NEW_FAIL_TXT = u"{lab_name:s}: new failure"

LAST_PASS_TXT = u"last pass: {good_kernel:s}"
LAST_PASS_HTML = \
    u"last pass: <a href=\"{boot_id_url:s}\">{good_kernel:s}</a>"

FIRST_FAIL_TXT = u"first fail: {bad_kernel:s}"
FIRST_FAIL_HTML = \
    u"first fail: <a href=\"{boot_id_url:s}\">{bad_kernel:s}</a>"


def create_regressions_data(boot_docs, boot_data):
    """Create the regressions data for the email report.

    Will create the TXT/HTML strings to be used in the report.

    :param boot_docs: The regressions data (the list of boot reports).
    :type boot_docs: list
    :param boot_data: Details about the boot results
    :type boot_data: dict
    :return dict The regressions strings in a dictionary.
    """
    regr_data = {}

    # Make sure the boot reports in the regressions data structure are
    # correctly sorted by date, so that the oldest document is the PASS one
    # and the most recent one is the last FAIL-ed.
    boot_docs.sort(
        cmp=lambda x, y: cmp(x[models.CREATED_KEY], y[models.CREATED_KEY]))

    last_fail = boot_docs[-1]
    last_good = boot_docs[0]

    fmt_data = {
        "boot_id_url": boot_data["boot_id_url"],
        "red": boot_data["red"],
        models.LAB_NAME_KEY: last_fail[models.LAB_NAME_KEY],
        "good_kernel": last_good[models.KERNEL_KEY],
        "boot_regressions_url": rcommon.BOOT_REGRESSIONS_URL.format(
            **boot_data),
    }

    fail_url = BOOT_ID_HTML.format(**fmt_data).format(**last_fail)

    if len(boot_docs) == 2:
        failure = NEW_FAIL_HTML.format(**fmt_data)

        # Simple case, it's a new failure.
        regr_data["txt"] = \
            u"{:s} ({:s})".format(
                NEW_FAIL_TXT.format(**last_fail),
                LAST_PASS_TXT.format(**fmt_data))
        regr_data["html"] = \
            u"{:s}: {:s} <small>({:s})</small>".format(
                fail_url,
                failure,
                LAST_PASS_HTML.format(**fmt_data).format(**last_good))
    else:
        # The first boot report is always a PASS status.
        first_fail = boot_docs[1]
        fmt_data["bad_kernel"] = first_fail[models.KERNEL_KEY]

        delta = last_fail[models.CREATED_KEY] - first_fail[models.CREATED_KEY]
        days = delta.days

        # Default to 1 day.
        if days == 0:
            days = 1
        # Inject the number of days.
        fmt_data["days"] = days

        failure_txt = P_(
            SINGULAR_FAILURE_TXT, PLURAL_FAILURE_TXT, days)\
            .format(**fmt_data)

        failure_html = P_(
            SINGULAR_FAILURE_HTML, PLURAL_FAILURE_HTML, days)\
            .format(**fmt_data)

        regr_data["txt"] = \
            u"{:s}: {:s} ({:s} - {:s})".format(
                last_fail[models.LAB_NAME_KEY],
                failure_txt,
                LAST_PASS_TXT.format(**fmt_data),
                FIRST_FAIL_TXT.format(**fmt_data))
        regr_data["html"] = \
            u"{:s}: {:s} <small>({:s} - {:s})</small>".format(
                fail_url,
                failure_html,
                LAST_PASS_HTML.format(**fmt_data).format(**last_good),
                FIRST_FAIL_HTML.format(**fmt_data).format(**first_fail))

    return regr_data


def parse_regressions(lab_regressions, boot_data, db_options):
    """Parse the regressions data and create the strings for the report.

    The returned data structure is:

        {
            "summary": {
                "txt": ["List of TXT summary strings"],
                "html: ["List of HTML summary strings"]
            },
            "data": {
                "arch": {
                    "defconfig": {
                        "build_environment": {
                            "board": [
                                {
                                    "txt": "string",
                                    "html": "string"
                                },
                            ]
                        }
                    }
                }
            }
        }

    :param lab_regressions: The regressions data for each lab.
    :type lab_regressions: dict
    :param boot_data: Details about the boot results
    :type boot_data: dict
    :return dict The regressions data structure for the report.
    """
    regressions = {}
    regressions_data = None
    bisections = []
    lab_name = boot_data.get("lab_name", None)

    for lab, lab_d in lab_regressions.iteritems():
        if lab_name and lab != lab_name:
            continue

        regressions_data = regressions.setdefault("data", {})

        for arch, arch_d in lab_d.iteritems():
            # Prepare the arch string for visualization.
            # Same for defconfig and board ones.
            arch = unicode(arch)
            regr_arch = regressions_data.setdefault(arch, {})

            for board, board_d in arch_d.iteritems():
                board = unicode(board)
                for instance_d in board_d.itervalues():
                    for defconfig, defconfig_d in instance_d.iteritems():
                        defconfig = unicode(defconfig)
                        regr_def = regr_arch.setdefault(defconfig, {})
                        for build_env, build_env_d in defconfig_d.iteritems():
                            regr_build_env = regr_def.setdefault(
                                build_env, {})
                            for compiler, boots in build_env_d.iteritems():
                                regr_board = regr_build_env.setdefault(
                                    board, [])
                                good, bad = boots[0], boots[-1]
                                bisect = bbisect.create_boot_bisect(
                                    good, bad, db_options)
                                bisections.append(bisect)
                                regr = create_regressions_data(
                                    boots, boot_data)
                                regr_board.append(regr)

    # Remove duplicate entries - they are dictionaries so filter them by _id
    bisections = {b['_id']: b for b in bisections}.values()

    if regressions_data:
        regressions["summary"] = {}
        regressions["summary"]["txt"] = ["Boot Regressions Detected:"]
        regressions["summary"]["html"] = ["Boot Regressions Detected:"]

    return regressions, bisections


def _update_boot_conflicts(data, spec, database):
    conflict_data = None
    conflict_count = 0
    fail_results = data["fail_results"]
    failed_data, _, _, unique_data = \
        _parse_boot_results(fail_results.clone(), get_unique=True)

    # Copy the failed results here. The mongodb Cursor, for some
    # reasons gets overwritten.
    fail_results = [x for x in fail_results.clone()]
    fail_count = data["fail_count"]

    if all([fail_count != data["total_count"], data["lab_name"] is None]):
        # If the number of failed boots differs from the total number of
        # boot reports, check if we have conflicting reports. We look
        # for boot reports that have the same attributes of the failed ones
        # but that indicate a PASS status.
        spec[models.STATUS_KEY] = models.PASS_STATUS
        for key, val in unique_data.iteritems():
            spec[key] = {"$in": val}

        if data["pass_count"] > 0:
            # If we have such boot reports, filter and aggregate them
            # together.
            def _conflicting_data():
                """Local generator function to search conflicting data.

                This is used to provide a filter mechanism during the list
                comprehension in order to exclude `None` values.
                """
                for failed, passed in itertools.product(
                        fail_results, pass_results.clone()):
                    yield _search_conflicts(failed, passed)

            pass_results = utils.db.find(
                database[models.BOOT_COLLECTION],
                0,
                0,
                spec=spec,
                fields=BOOT_SEARCH_FIELDS,
                sort=BOOT_SEARCH_SORT
            )

            # zip() is its own inverse, when using the * operator.
            # We get back (failed,passed) tuples during the list
            # comprehension, but we need a list of values not tuples.
            # unzip it, and then chain the two resulting tuples together.
            conflicting_tuples = zip(*(
                x for x in _conflicting_data()
                if x is not None
            ))

            # Make sure we do not have an empty list here after filtering.
            if conflicting_tuples:
                conflicts = itertools.chain(
                    conflicting_tuples[0], conflicting_tuples[1])
                conflict_data, failed_data, conflict_count, _ = \
                    _parse_boot_results(conflicts,
                                        intersect_results=failed_data)

    data.update({
        "failed_data": failed_data,
        "conflict_data": conflict_data,
        "conflict_count": conflict_count,
        "fail_count": fail_count - conflict_count,
    })


def get_boot_data(db_options, job, branch, kernel, lab_name):
    total_count, total_unique_data = rcommon.get_total_results(
        job,
        branch,
        kernel,
        models.BOOT_COLLECTION,
        db_options,
        lab_name
    )

    total_builds = rcommon.get_total_results(
        job,
        branch,
        kernel,
        models.BUILD_COLLECTION,
        db_options
    )[0]

    git_commit, git_url = rcommon.get_git_data(job, branch, kernel, db_options)

    spec = {
        models.JOB_KEY: job,
        models.GIT_BRANCH_KEY: branch,
        models.KERNEL_KEY: kernel,
        models.STATUS_KEY: models.OFFLINE_STATUS
    }

    if lab_name:
        spec[models.LAB_NAME_KEY] = lab_name

    database = utils.db.get_db_connection(db_options)

    offline_results, offline_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT
    )

    # MongoDB cursor gets overwritten somehow by the next query. Extract the
    # data before this happens.
    offline_data = None
    if offline_count > 0:
        offline_data = _parse_boot_results(offline_results.clone())[0]

    spec[models.STATUS_KEY] = {
        "$in": [models.UNTRIED_STATUS, models.UNKNOWN_STATUS]
    }
    untried_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT
    )[1]

    spec[models.STATUS_KEY] = models.FAIL_STATUS
    fail_results, fail_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT
    )

    # Calculate the PASS count based on the previous obtained values.
    pass_count = total_count - fail_count - offline_count - untried_count

    # Fill the boot data structure
    data = {
        "base_url": rcommon.DEFAULT_BASE_URL,
        "boot_url": rcommon.DEFAULT_BOOT_URL,
        "build_url": rcommon.DEFAULT_BUILD_URL,
        "conflict_count": 0,
        "conflict_data": None,
        "fail_results": fail_results,
        "fail_count": fail_count,
        "failed_data": None,
        "git_branch": branch,
        "git_commit": git_commit,
        "git_url": git_url,
        "offline_count": offline_count,
        "offline_data": offline_data,
        "pass_count": pass_count,
        "total_builds": total_builds,
        "total_count": total_count,
        "total_unique_data": total_unique_data,
        "untried_count": untried_count,
        "red": rcommon.HTML_RED,
        "boot_id_url": rcommon.BOOT_ID_URL,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.LAB_NAME_KEY: lab_name
    }

    # Get the regressions and determine which bisections to run.
    regressions_doc = database[models.BOOT_REGRESSIONS_COLLECTION].find_one(
        {models.JOB_KEY: job, models.KERNEL_KEY: kernel})

    if regressions_doc:
        data["regressions"], data["bisections"] = parse_regressions(
            regressions_doc[models.REGRESSIONS_KEY], data, db_options)
    else:
        data["regressions"], data["bisections"] = None, None

    if fail_count > 0:
        _update_boot_conflicts(data, spec, database)

    return data


# pylint: disable=too-many-locals
# pylint: disable=star-args
# pylint: disable=too-many-arguments
def create_boot_report(
        job,
        branch,
        kernel, lab_name, email_format, db_options, mail_options=None):
    """Create the boot report email to be sent.

    If lab_name is not None, it will trigger a boot report only for that
    specified lab.

    :param job: The name of the job.
    :type job: string
    :param  kernel: The name of the kernel.
    :type kernel: string
    :param lab_name: The name of the lab.
    :type lab_name: string
    :param email_format: The email format to send.
    :type email_format: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    :return A tuple with the TXT email body, the HTML email body and the
    subject as strings or None.
    """
    boot_data = get_boot_data(db_options, job, branch, kernel, lab_name)

    # Email TXT and HTML body.
    txt_body = None
    html_body = None
    subject = None

    # This is used to provide a footer note in the email report.
    info_email = mail_options.get("info_email", None) if mail_options else None

    boot_data.update({
        "email_format": email_format,
        "info_email": info_email,
    })

    custom_headers = {
        rcommon.X_REPORT: rcommon.BOOT_REPORT_TYPE,
        rcommon.X_BRANCH: branch,
        rcommon.X_TREE: job,
        rcommon.X_KERNEL: kernel,
    }

    if lab_name:
        custom_headers[rcommon.X_LAB] = lab_name

    if boot_data["fail_count"] or boot_data["total_count"]:
        txt_body, html_body, subject = _create_boot_email(boot_data)
    else:
        utils.LOG.warn(
            "Nothing found for '%s-%s-%s': no email report sent",
            job, branch, kernel)
        txt_body = html_body = subject = None

    return txt_body, html_body, subject, custom_headers


def _start_bisection(bisection, jopts):
    params_map = {
        "KERNEL_URL": models.GIT_URL_KEY,
        "KERNEL_BRANCH": models.GIT_BRANCH_KEY,
        "ARCH": models.ARCHITECTURE_KEY,
        "DEFCONFIG": models.DEFCONFIG_FULL_KEY,
        "TARGET": models.DEVICE_TYPE_KEY,
        "LAB": models.LAB_NAME_KEY,
        "KERNEL_TREE": models.JOB_KEY,
        "KERNEL_NAME": models.KERNEL_KEY,
        "GOOD_COMMIT": models.BISECT_GOOD_COMMIT_KEY,
        "BAD_COMMIT": models.BISECT_BAD_COMMIT_KEY,
        "CC": models.COMPILER_KEY,
        "CC_VERSION": models.COMPILER_VERSION_KEY,
        "BUILD_ENVIRONMENT": models.BUILD_ENVIRONMENT_KEY,
    }
    params = {
        k: v for (k, v) in (
            (k, bisection.get(x)) for k, x in params_map.iteritems()) if v
    }
    utils.LOG.info("Triggering bisection for {}/{}, board: {}, lab: {}".format(
        params["KERNEL_TREE"], params["KERNEL_BRANCH"],
        params["TARGET"], params["LAB"]))
    server = jenkins.Jenkins(jopts["url"], jopts["user"], jopts["token"])
    server.build_job(jopts["bisect"], params)


def trigger_bisections(status, job, branch, kernel, lab_name,
                       db_options, jenkins_options):
    if not jenkins_options:
        return "SKIP"

    boot_data = get_boot_data(db_options, job, branch, kernel, lab_name)
    bisections = boot_data.get("bisections")
    if not bisections:
        return "OK"

    # We need to make some changes in-place but not modify incoming data
    bisections = copy.copy(bisections)

    # Shuffle the bisections in random order to avoid running ones targetting
    # the same board at the same time and also to avoid any kind of dependency
    # on the order in which they are being generated.
    random.shuffle(bisections)

    # Group similar bisections together to only run a subset of them
    similar_bisections = {}
    for b in bisections:
        key = (
            b[models.BISECT_GOOD_COMMIT_KEY],
            b[models.BISECT_BAD_COMMIT_KEY],
        )
        blist = similar_bisections.setdefault(key, [])
        blist.append(b)
    bisections = []
    for b in similar_bisections.values():
        bisections.extend(b[:3])

    # Now trigger the bisections
    for b in bisections:
        try:
            _start_bisection(b, jenkins_options)
        except Exception, e:
            utils.LOG.error("Failed to start bisection: {}".format(e))

    return "OK"


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def _parse_boot_results(results, intersect_results=None, get_unique=False):
    """Parse the boot results from the database creating a new data structure.

    This is done to provide a simpler data structure to create the email
    body.

    If `get_unique` is True, it will return also a dictionary with unique
    values found in the passed `results` for `arch`, `board` and
    `defconfig_full` keys.

    :param results: The boot results to parse.
    :type results: `pymongo.cursor.Cursor` or a list of dict
    :param get_unique: Return the unique values in the data structure. Default
    to False.
    :type get_unique: bool
    :param intersect_results: The boot results to remove intersecting items.
    :type intersect_results: dict
    :return A tuple with the parsed data as dictionary, a tuple of data as
    a dictionary that has had intersecting entries removed or None, the number
    of intersections found or 0, and the unique data or None.
    """
    parsed_data = {}
    unique_data = None
    intersections = 0

    if get_unique:
        unique_data = rcommon.get_unique_data(results)

    for result in results:
        res_get = result.get

        lab_name = res_get(models.LAB_NAME_KEY)
        board = res_get(models.BOARD_KEY)
        arch = res_get(models.ARCHITECTURE_KEY)
        defconfig = res_get(models.DEFCONFIG_FULL_KEY)
        status = res_get(models.STATUS_KEY)
        build_env = res_get(models.BUILD_ENVIRONMENT_KEY)

        result_struct = {
            arch: {
                defconfig: {
                    build_env: {
                        board: {
                            lab_name: status
                        }
                    }
                }
            }
        }

        # Check if the current result intersects the other interect_results
        if intersect_results:
            arch_view = intersect_results.viewkeys()

            if arch in arch_view:
                defconfig_view = intersect_results[arch].viewkeys()

                if defconfig in defconfig_view:
                    build_env_view = \
                        intersect_results[arch][defconfig].viewkeys()
                    irad = intersect_results[arch][defconfig]
                    if build_env in build_env_view:
                        if irad[build_env].get(board, None):
                            intersections += 1
                            del irad[build_env][board]
                            # Clean up also the remainder of the data structure
                            # so that we really have cleaned up data.
                            if not irad[build_env]:
                                del irad[build_env]
                            if not intersect_results[arch][defconfig]:
                                del intersect_results[arch][defconfig]
                            if not intersect_results[arch]:
                                del intersect_results[arch]

        if arch in parsed_data:
            if defconfig in parsed_data[arch]:
                if build_env in parsed_data[arch][defconfig]:
                    if board in parsed_data[arch][defconfig][build_env]:
                        pdad = parsed_data[arch][defconfig]
                        pdadb = pdad[build_env]
                        rsad = result_struct[arch][defconfig]
                        if lab_name not in pdadb[board]:
                            pdadb[board][lab_name] = \
                                rsad[build_env][board][lab_name]
                    else:
                        parsed_data[arch][defconfig][build_env][board] = \
                            result_struct[arch][defconfig][build_env][board]
                else:
                    parsed_data[arch][defconfig][build_env] = \
                        result_struct[arch][defconfig][build_env]
            else:
                parsed_data[arch][defconfig] = result_struct[arch][defconfig]
        else:
            parsed_data[arch] = result_struct[arch]

    return parsed_data, intersect_results, intersections, unique_data


def _search_conflicts(failed, passed):
    """Make sure the failed and passed results are a conflict and return it.

    If they are not a conflict, return `None`.

    :param failed: The failed result.
    :type failed: dict
    :param passed: The passed result.
    :type passed: dict
    :return The conflict (the passed result) or `None`.
    """
    conflict = None
    fail_get = failed.get
    pass_get = passed.get

    def _is_valid_pair(f_g, p_g):
        """If the failed and passed values are a valid pair.

        A valid pair means that:
          Their `_id` values are different
          Their `lab_name` values are different
          They have the same `board`, `arch`, `defconfig_full` and
          `build_environment` values

        :param f_g: The `get` function for the `failed` result.
        :type f_g: function
        :param p_g: The `get` function for the `passed` result.
        :return True or False.
        """
        is_valid = False
        if (f_g(models.ID_KEY) != p_g(models.ID_KEY) and
                f_g(models.LAB_NAME_KEY) != p_g(models.LAB_NAME_KEY) and
                f_g(models.BOARD_KEY) == p_g(models.BOARD_KEY) and
                f_g(models.ARCHITECTURE_KEY) ==
                p_g(models.ARCHITECTURE_KEY) and
                f_g(models.DEFCONFIG_FULL_KEY) ==
                p_g(models.DEFCONFIG_FULL_KEY) and
                f_g(models.BUILD_ENVIRONMENT_KEY) ==
                p_g(models.BUILD_ENVIRONMENT_KEY)):
            is_valid = True
        return is_valid

    if _is_valid_pair(fail_get, pass_get):
        if fail_get(models.STATUS_KEY) != pass_get(models.STATUS_KEY):
            conflict = failed, passed

    return conflict


def get_boot_subject_string(boot_data):
    """Create the boot email subject line.

    This is used to created the custom email report line based on the number
    of values we have.

    :param boot_data: Details about the boot results
    :type boot_data: dict
    :return The subject string.
    """
    b_get = boot_data.get
    conflict_count = b_get("conflict_count", 0)
    fail_count = b_get("fail_count", 0)
    lab_name = b_get("lab_name", None)
    offline_count = b_get("offline_count", 0)
    pass_count = b_get("pass_count", 0)
    total_count = b_get("total_count", 0)
    untried_count = b_get("untried_count", 0)

    subject_str = u""
    base_subject = G_(u"{job:s}/{git_branch:s} boot")
    total_boots = P_(
        u"{total_count:d} boot", u"{total_count:d} boots", total_count)
    passed_boots = G_(u"{pass_count:d} passed")
    failed_boots = G_(u"{fail_count:d} failed")
    conflict_boots = P_(
        u"{conflict_count:d} conflict",
        u"{conflict_count:d} conflicts",
        conflict_count
    )
    offline_boots = G_(u"{offline_count:d} offline")
    kernel_name = G_(u"({kernel:s})")
    lab_description = G_(u"{lab_name:s}")
    untried_boots = G_(u"{untried_count:d} untried/unknown")

    # Base format strings to create the subject line.
    # 1st, 2nd, 3rd and 4th are replaced with job name, total, failed, passed.
    # The last is the kernel/git-describe value:
    # next boot: 10 boots: 1 failed, 9 passed (next-20990101)
    base_0 = G_(u"{:s}: {:s}: {:s}, {:s} {:s}")
    # next boot: 10 boots: 0 failed, 0 passed, 10 offline (next-20990101)
    base_1 = G_(u"{:s}: {:s}: {:s}, {:s}, {:s} {:s}")
    # next boot: 10 boots: 1 failed, 8 passed with 1 offline (next-20990101)
    base_2 = G_(u"{:s}: {:s}: {:s}, {:s} with {:s} {:s}")
    # next boot: 10 boots: 1 failed, 7 passed with 1 offline,
    # 1 untried/unknown (next-20990101)
    # next boot: 10 boots: 1 failed, 6 passed with 1 offline,
    # 1 untried/unknown, 1 conflict (next-20990101)
    base_3 = G_(u"{:s}: {:s}: {:s}, {:s} with {:s}, {:s} {:s}")
    base_4 = G_(u"{:s}: {:s}: {:s}, {:s} with {:s}, {:s}, {:s} {:s}")

    # Here the last is the lab name.
    base_lab_0 = G_(u"{:s}: {:s}: {:s}, {:s} {:s} - {:s}")
    base_lab_1 = G_(u"{:s}: {:s}: {:s}, {:s}, {:s} {:s} - {:s}")
    base_lab_2 = G_(u"{:s}: {:s}: {:s}, {:s} with {:s} {:s} - {:s}")
    base_lab_3 = G_(u"{:s}: {:s}: {:s}, {:s} with {:s}, {:s} {:s} - {:s}")
    base_lab_4 = G_(
        u"{:s}: {:s}: {:s}, {:s} with {:s}, {:s}, {:s} {:s} - {:s}")

    if total_count == pass_count and total_count == fail_count:
        # Everything is good or failed.
        if lab_name:
            subject_str = base_lab_0.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, kernel_name, lab_description)
        else:
            subject_str = base_0.format(
                base_subject,
                total_boots, failed_boots, passed_boots, kernel_name)
    elif total_count == offline_count:
        # Everything is offline.
        if lab_name:
            subject_str = base_lab_1.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, offline_boots, kernel_name, lab_description)
        else:
            subject_str = base_1.format(
                base_subject,
                total_boots,
                failed_boots, passed_boots, offline_boots, kernel_name)
    elif total_count == untried_count:
        # Everything is untried/unknown.
        if lab_name:
            subject_str = base_lab_1.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, untried_boots, kernel_name, lab_description)
        else:
            subject_str = base_1.format(
                base_subject,
                total_boots,
                failed_boots, passed_boots, untried_boots, kernel_name)
    elif (untried_count == 0 and offline_count == 0 and conflict_count == 0):
        # Passed and failed.
        if lab_name:
            subject_str = base_lab_0.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, kernel_name, lab_description)
        else:
            subject_str = base_0.format(
                base_subject,
                total_boots, failed_boots, passed_boots, kernel_name)
    elif untried_count > 0 and offline_count == 0 and conflict_count == 0:
        # Passed, failed and untried.
        if lab_name:
            subject_str = base_lab_2.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, untried_boots, kernel_name, lab_description)
        else:
            subject_str = base_2.format(
                base_subject,
                total_boots,
                failed_boots, passed_boots, untried_boots, kernel_name)
    elif untried_count > 0 and offline_count > 0 and conflict_count == 0:
        # Passed, failed, untried and offline.
        if lab_name:
            subject_str = base_lab_3.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots,
                offline_boots, untried_boots, kernel_name, lab_description)
        else:
            subject_str = base_3.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, offline_boots, untried_boots, kernel_name)
    elif untried_count > 0 and offline_count > 0 and conflict_count > 0:
        # Passed, failed, untried and offline with conflict.
        if lab_name:
            subject_str = base_lab_4.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots,
                offline_boots,
                untried_boots, conflict_boots, kernel_name, lab_description)
        else:
            subject_str = base_4.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots,
                offline_boots, untried_boots, conflict_boots, kernel_name)
    elif untried_count == 0 and offline_count > 0 and conflict_count == 0:
        # Passed, failed and offline.
        if lab_name:
            subject_str = base_lab_2.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, offline_boots, kernel_name, lab_description)
        else:
            subject_str = base_2.format(
                base_subject,
                total_boots,
                failed_boots, passed_boots, offline_boots, kernel_name)
    elif untried_count == 0 and offline_count > 0 and conflict_count > 0:
        # Passed, failed, offline with conflicts.
        if lab_name:
            subject_str = base_lab_3.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots,
                offline_boots, conflict_boots, kernel_name, lab_description)
        else:
            subject_str = base_3.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, offline_boots, conflict_boots, kernel_name)
    elif untried_count == 0 and offline_count == 0 and conflict_count > 0:
        # Passed, failed with conflicts.
        if lab_name:
            subject_str = base_lab_2.format(
                base_subject,
                total_boots,
                failed_boots,
                passed_boots, conflict_boots, kernel_name, lab_description)
        else:
            subject_str = base_2.format(
                base_subject,
                total_boots,
                failed_boots, passed_boots, conflict_boots, kernel_name)

    # Now fill in the values.
    subject_str = subject_str.format(**boot_data)

    return subject_str


def _create_boot_email(boot_data):
    """Parse the results and create the email text body to send.

    :param boot_data: Details about the boot results
    :type boot_data: dict
    :return A tuple with the email body and subject as strings.
    """
    txt_body = None
    html_body = None
    subject_str = None

    b_get = boot_data.get
    total_unique_data = b_get("total_unique_data", None)
    info_email = b_get("info_email", None)
    email_format = b_get("email_format")

    subject_str = get_boot_subject_string(boot_data)

    tested_one = G_(u"Tested: {:s}")
    tested_two = G_(u"Tested: {:s}, {:s}")
    tested_three = G_(u"Tested: {:s}, {:s}, {:s}")

    tested_string = None
    if total_unique_data:
        unique_boards = rcommon.count_unique(
            total_unique_data.get(models.BOARD_KEY, None))
        unique_socs = rcommon.count_unique(
            total_unique_data.get(models.MACH_KEY, None))
        unique_builds = rcommon.count_unique(
            total_unique_data[models.DEFCONFIG_FULL_KEY])

        boot_data["unique_boards"] = unique_boards
        boot_data["unique_socs"] = unique_socs
        boot_data["unique_builds"] = unique_builds

        boards_str = P_(
            u"{unique_boards:d} unique board",
            u"{unique_boards:d} unique boards",
            unique_boards
        )
        soc_str = P_(
            u"{unique_socs:d} SoC family",
            u"{unique_socs:d} SoC families",
            unique_socs
        )
        builds_str = P_(
            u"{unique_builds:d} build out of {total_builds:d}",
            u"{unique_builds:d} builds out of {total_builds:d}",
            unique_builds
        )

        if unique_boards > 0 and unique_socs > 0 and unique_builds > 0:
            tested_string = tested_three.format(
                boards_str, soc_str, builds_str)
        elif unique_boards > 0 and unique_socs > 0 and unique_builds == 0:
            tested_string = tested_two.format(boards_str, soc_str)
        elif unique_boards > 0 and unique_socs == 0 and unique_builds > 0:
            tested_string = tested_two.format(boards_str, builds_str)
        elif unique_boards == 0 and unique_socs > 0 and unique_builds > 0:
            tested_string = tested_two.format(soc_str, builds_str)
        elif unique_boards > 0 and unique_socs == 0 and unique_builds == 0:
            tested_string = tested_one.format(boards_str)
        elif unique_boards == 0 and unique_socs > 0 and unique_builds == 0:
            tested_string = tested_one.format(soc_str)
        elif unique_boards == 0 and unique_socs == 0 and unique_builds > 0:
            tested_string = tested_one.format(builds_str)

        if tested_string:
            tested_string = tested_string.format(**boot_data)

    boot_summary_url = rcommon.BOOT_SUMMARY_URL.format(**boot_data)
    build_summary_url = rcommon.BUILD_SUMMARY_URL.format(**boot_data)

    boot_data["tree_string"] = G_(u"Tree: {job:s}").format(**boot_data)
    boot_data["branch_string"] = G_(u"Branch: {git_branch:s}").format(
        **boot_data)
    boot_data["git_describe_string"] = G_(u"Git Describe: {kernel:s}").format(
        **boot_data)
    boot_data["info_email"] = info_email
    boot_data["tested_string"] = tested_string
    boot_data["subject_str"] = subject_str

    git_url = b_get("git_url")
    git_commit = b_get("git_commit")

    translated_git_url = \
        rcommon.translate_git_url(git_url, git_commit) or git_url

    git_txt_string = G_(u"Git URL: {:s}").format(git_url)
    git_html_string = G_(u"Git URL: <a href=\"{:s}\">{:s}</a>").format(
        translated_git_url, git_url)

    boot_data["git_commit_string"] = G_(u"Git Commit: {:s}").format(git_commit)
    boot_data["git_url_string"] = (git_txt_string, git_html_string)

    boot_data["platforms"] = _parse_and_structure_results(boot_data)

    if models.EMAIL_TXT_FORMAT_KEY in email_format:
        boot_data["full_boot_summary"] = (
            G_(u"Full Boot Summary: {:s}").format(boot_summary_url))
        boot_data["full_build_summary"] = (
            G_(u"Full Build Summary: {:s}").format(build_summary_url))

        txt_body = rcommon.create_txt_email("boot.txt", **boot_data)

    if models.EMAIL_HTML_FORMAT_KEY in email_format:
        # Fix the summary URLs for the HTML email.
        boot_data["full_boot_summary"] = (
            G_(u"Full Boot Summary: <a href=\"{url:s}\">{url:s}</a>").format(
                **{"url": boot_summary_url})
        )
        boot_data["full_build_summary"] = (
            G_(u"Full Build Summary: <a href=\"{url:s}\">{url:s}</a>").format(
                **{"url": build_summary_url})
        )

        html_body = rcommon.create_html_email("boot.html", **boot_data)

    return txt_body, html_body, subject_str


def _parse_and_structure_results(boot_data):
    """Parse the results and create a data structure for the templates.

    Create a special data structure to be consumed by the template engine.
    By default it will create the strings for TXT and HTML templates. The
    special template will then use the correct format.

    The template data structure is as follows for the normal case
    (not a conflict):

        {
            "summary": {
                "txt": ["List of TXT summary strings"],
                "html: ["List of HTML summary strings"]
            },
            "data": {
                "arch": {
                    "defconfig": {
                        "build_environment": {
                            "board": [("TXT version", "HTML version")]
                        }
                    }
                }
            }
        }

    In case of a conflict:

        {
            "summary": {
                "txt": ["List of TXT summary strings"],
                "html: ["List of HTML summary strings"]
            },
            "data": {
                "arch": {
                    "defconfig": {
                        "board": {
                            ("TXT version", "HTML version")
                        }
                    }
                }
            }
        }

    :param boot_data: Details about the boot results
    :type boot_data: dict
    :return The template data structure as a dictionary object.
    """
    b_get = boot_data.get

    offline_data = b_get("offline_data", None)
    failed_data = b_get("failed_data", None)
    conflict_data = b_get("conflict_data", None)
    fail_count = b_get("fail_count", 0)
    conflict_count = b_get("conflict_count", 0)

    parsed_data = {}

    def _traverse_data_struct(data,
                              data_struct,
                              is_conflict=False, is_offline=False):
        """Traverse the data structure and write it to file.

        :param data: The data structure to parse.
        :type data: dict
        :param data_struct: The data structure where the resuls will be stored.
        :type data_struct: dict
        :param is_conflict: If the data passed has to be considered a conflict
        aggregation.
        :type is_conflict: bool
        :param is_offline: If the data passed has to be considered an offline
        aggregation.
        :type is_offline: bool
        """
        d_get = data.get
        s_get = data_struct.get

        for arch in data.viewkeys():
            arch_string = G_(u"{:s}").format(arch)
            data_struct[arch_string] = {}

            arch_struct = s_get(arch_string)

            # Force defconfs to be sorted.
            defconfs = list(d_get(arch).viewkeys())
            defconfs.sort()

            for defconfig in defconfs:
                defconfig_string = G_(u"{:s}").format(defconfig)

                def_get = d_get(arch)[defconfig].get

                # Force build_envs to be sorted.
                build_envs = list(d_get(arch)[defconfig].viewkeys())
                build_envs.sort()

                for build_environment in build_envs:
                    build_environment_string = \
                        G_(u"{:s}").format(build_environment)

                    build_get = d_get(arch)[defconfig][build_environment].get
                    # Force boards to be sorted.
                    boards = list(
                        d_get(arch)[defconfig][build_environment].viewkeys()
                        )
                    boards.sort()

                    if is_conflict:
                        # For conflict, we need a dict as data structure,
                        # since we list boards and labs.
                        arch_struct[defconfig_string] = {}
                        defconf_struct = arch_struct[defconfig_string]

                        for board in boards:
                            # Copy the boot_data parameters and add the local
                            # ones.
                            # This is needed to create the HTML version of some
                            # of the values we are parsing.
                            substitutions = boot_data.copy()
                            substitutions["board"] = board
                            substitutions["defconfig"] = defconfig

                            board_url = \
                                rcommon.BOARD_URL.format(**substitutions)
                            substitutions["url"] = board_url

                            html_string = (
                                G_(
                                    u"<a href=\"{url:s}\">{board:s}</a>"
                                    ).format(
                                        **substitutions
                                        )
                                )
                            txt_string = G_(u"{:s}").format(board)

                            defconf_struct[(txt_string, html_string)] = []
                            board_struct = defconf_struct[
                                (txt_string, html_string)
                            ]
                            for lab in build_get(board).viewkeys():
                                board_struct.append((
                                    G_(u"{:s}: {:s}").format(
                                        lab, build_get(board)[lab]),
                                    build_environment
                                ))
                    else:
                        # Not a conflict data structure, we show only the count
                        # of the failed labs, not which one failed.

                        # For non-conflict, we need a list as data structure,
                        # since we only list the counts.
                        build_env_struct = []
                        arch_struct[defconfig_string] = {}
                        defconf_struct = arch_struct[defconfig_string]
                        defconf_struct[build_environment_string] = \
                            build_env_struct

                        for board in boards:
                            lab_count = 0
                            for lab in build_get(board).viewkeys():
                                lab_count += 1

                            if is_offline:
                                lab_count_str = (
                                    P_(
                                        "{:d} offline lab",
                                        "{:d} offline labs", lab_count
                                    ).format(lab_count)
                                )
                            else:
                                lab_count_str = (
                                    P_(
                                        "{:d} failed lab",
                                        "{:d} failed labs", lab_count
                                    ).format(lab_count)
                                )

                            # Copy the boot_data parameters and add the local
                            # ones.
                            # This is needed to create the HTML version of some
                            # of the values we are parsing.
                            substitutions = boot_data.copy()
                            substitutions["board"] = board
                            substitutions["defconfig"] = defconfig

                            board_url = \
                                rcommon.BOARD_URL.format(**substitutions)
                            substitutions["url"] = board_url
                            substitutions["count"] = lab_count_str

                            html_string = (
                                G_(
                                    u"<a href=\"{url:s}\">" +
                                    u"{board:s}</a>: {count:s}"
                                ).format(**substitutions))

                            txt_string = G_(u"{:s}: {:s}").format(
                                board, lab_count_str)
                            build_env_struct.append((txt_string, html_string))

    if failed_data:
        parsed_data["failed_data"] = {}
        failed_struct = parsed_data["failed_data"]

        failed_struct["data"] = {}
        failed_struct["summary"] = {}
        failed_struct["summary"]["txt"] = []
        failed_struct["summary"]["html"] = []

        boot_failure_url = \
            u"{base_url:s}/boot/?{kernel:s}&fail".format(**boot_data)
        boot_failure_url_html = (
            u"<a href=\"{boot_failure_url:s}\">"
            u"{boot_failure_url:s}</a>".format(
                **{"boot_failure_url": boot_failure_url})
        )
        failed_summary = P_(
            u"Boot Failure Detected:", u"Boot Failures Detected:", fail_count)

        failed_struct["summary"]["txt"].append(
            failed_summary.format(**{"boot_failure_url": boot_failure_url}))

        failed_struct["summary"]["html"].append(
            failed_summary.format(
                **{"boot_failure_url": boot_failure_url_html}))

        _traverse_data_struct(failed_data, failed_struct["data"])
    else:
        parsed_data["failed_data"] = None

    if offline_data:
        parsed_data["offline_data"] = {}
        offline_struct = parsed_data["offline_data"]

        offline_struct["data"] = {}
        offline_struct["summary"] = {}
        offline_struct["summary"]["txt"] = []
        offline_struct["summary"]["html"] = []

        summary = G_(u"Offline Platforms:")
        offline_struct["summary"]["txt"].append(summary)
        offline_struct["summary"]["html"].append(summary)

        _traverse_data_struct(
            offline_data, offline_struct["data"], is_offline=True)
    else:
        parsed_data["offline_data"] = None

    if conflict_data:
        parsed_data["conflict_data"] = {}
        conflict_struct = parsed_data["conflict_data"]

        conflict_struct["data"] = {}
        conflict_struct["summary"] = {}
        conflict_struct["summary"]["txt"] = []
        conflict_struct["summary"]["html"] = []

        conflict_comment = G_(
            u"(These likely are not failures as other labs are reporting "
            "PASS. Needs review.)")
        conflict_summary = (
            P_(
                u"Conflicting Boot Failure Detected: {:s}",
                u"Conflicting Boot Failures Detected: {:s}",
                conflict_count
            ).format(conflict_comment)
        )

        conflict_struct["summary"]["txt"].append(conflict_summary)
        conflict_struct["summary"]["html"].append(conflict_summary)

        _traverse_data_struct(
            conflict_data, conflict_struct["data"], is_conflict=True)
    else:
        parsed_data["conflict_data"] = None
    return parsed_data
