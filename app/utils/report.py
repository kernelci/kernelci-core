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

"""Create and send email reports."""

import gettext
import io
import itertools
import pymongo
import types

import models
import models.report as mreport
import utils
import utils.db

# Register the translation domain and fallback safely, at the moment we do
# not care if we have translations or not, we just use gettext to exploit its
# plural forms capabilities. We mark the email string as translatable though
# so we might give that feature in the future.
t = gettext.translation("kernelci-backed", fallback=True)
# Register normal Unicode gettext.
_ = t.ugettext
# Register plural forms Unicode gettext.
_p = t.ungettext

DEFAULT_BASE_URL = u"http://kernelci.org"
DEFAULT_BOOT_URL = u"http://kernelci.org/boot/all/job"
DEFAULT_BUILD_URL = u"http://kernelci.org/build"

BOOT_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.LAB_NAME_KEY,
    models.MACH_KEY,
    models.STATUS_KEY
]

BUILD_SEARCH_FIELDS = [
    models.GIT_COMMIT_KEY,
    models.GIT_URL_KEY,
    models.GIT_BRANCH_KEY
]

BOOT_SEARCH_SORT = [
    (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
    (models.BOARD_KEY, pymongo.ASCENDING)
]


# pylint: disable=too-many-arguments
# pylint: disable=star-args
def save_report(job, kernel, r_type, status, errors, db_options):
    """Save the report in the database.

    :param job: The job name.
    :type job: str
    :param kernel: The kernel name.
    :type kernel: str
    :param r_type: The type of report to save.
    :type r_type: str
    :param status: The status of the send action.
    :type status: str
    :param errors: A list of errors from the send action.
    :type errors: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    utils.LOG.info("Saving '%s' report for '%s-%s'", r_type, job, kernel)

    name = "%s-%s" % (job, kernel)

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.NAME_KEY: name,
        models.TYPE_KEY: r_type
    }

    database = utils.db.get_db_connection(db_options)

    prev_doc = utils.db.find_one2(
        database[models.REPORT_COLLECTION], spec_or_id=spec)

    if prev_doc:
        report = mreport.ReportDocument.from_json(prev_doc)
        report.status = status
        report.errors = errors

        utils.db.save(database, report)
    else:
        report = mreport.ReportDocument(name)
        report.job = job
        report.kernel = kernel
        report.r_type = r_type
        report.status = status
        report.errors = errors

        utils.db.save(database, report, manipulate=True)


# pylint: disable=too-many-locals
def create_boot_report(job, kernel, lab_name, db_options, mail_options=None):
    """Create the boot report email to be sent.

    If lab_name is not None, it will trigger a boot report only for that
    specified lab.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param lab_name: The name of the lab.
    :type lab_name: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param mail_options: The options necessary to connect to the SMTP server.
    :type mail_options: dict
    :return A tuple with the email body and subject as strings or None.
    """
    kwargs = {}
    email_body = None
    subject = None
    # This is used to provide a footer note in the email report.
    info_email = None

    if mail_options:
        info_email = mail_options.get("info_email", None)

    database = utils.db.get_db_connection(db_options)

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
    }

    if lab_name is not None:
        spec[models.LAB_NAME_KEY] = lab_name

    total_results, total_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=[models.ID_KEY])

    total_unique_data = _get_unique_data(total_results.clone())

    git_results = utils.db.find(
        database[models.JOB_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BUILD_SEARCH_FIELDS)

    git_data = _parse_job_results(git_results)
    if git_data:
        git_commit = git_data[models.GIT_COMMIT_KEY]
        git_url = git_data[models.GIT_URL_KEY]
        git_branch = git_data[models.GIT_BRANCH_KEY]
    else:
        git_commit = git_url = git_branch = u"Unknown"

    spec[models.STATUS_KEY] = models.OFFLINE_STATUS

    offline_results, offline_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT)

    # MongoDB cursor gets overwritten somehow by the next query. Extract the
    # data before this happens.
    if offline_count > 0:
        offline_data, _, _, _ = _parse_boot_results(offline_results.clone())
    else:
        offline_data = None

    spec[models.STATUS_KEY] = models.FAIL_STATUS

    fail_results, fail_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT)

    failed_data = None
    conflict_data = None
    conflict_count = 0

    # Fill the data structure for the email report creation.
    kwargs = {
        "base_url": DEFAULT_BASE_URL,
        "boot_url": DEFAULT_BOOT_URL,
        "build_url": DEFAULT_BUILD_URL,
        "conflict_count": conflict_count,
        "conflict_data": conflict_data,
        "fail_count": fail_count - conflict_count,
        "failed_data": failed_data,
        "git_branch": git_branch,
        "git_commit": git_commit,
        "git_url": git_url,
        "info_email": info_email,
        "offline_count": offline_count,
        "offline_data": offline_data,
        "pass_count": total_count - fail_count - offline_count,
        "total_count": total_count,
        "total_unique_data": total_unique_data,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.LAB_NAME_KEY: lab_name
    }

    if fail_count > 0:
        failed_data, _, _, unique_data = \
            _parse_boot_results(fail_results.clone(), get_unique=True)

        # Copy the failed results here. The mongodb Cursor, for some
        # reasons gets overwritten.
        fail_results = [x for x in fail_results.clone()]

        conflict_data = None
        if all([fail_count != total_count, lab_name is None]):
            # If the number of failed boots differs from the total number of
            # boot reports, check if we have conflicting reports. We look
            # for boot reports that have the same attributes of the failed ones
            # but that indicate a PASS status.
            spec[models.STATUS_KEY] = models.PASS_STATUS
            for key, val in unique_data.iteritems():
                spec[key] = {"$in": val}

            pass_results, pass_count = utils.db.find_and_count(
                database[models.BOOT_COLLECTION],
                0,
                0,
                spec=spec,
                fields=BOOT_SEARCH_FIELDS,
                sort=BOOT_SEARCH_SORT)

            if pass_count > 0:
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

                # zip() is its own inverse, when using the * operator.
                # We get back (failed,passed) tuples during the list
                # comprehension, but we need a list of values not tuples.
                # unzip it, and then chain the two resulting tuples together.
                conflicting_tuples = zip(*(
                    x for x in _conflicting_data()
                    if x is not None
                ))

                conflicts = itertools.chain(
                    conflicting_tuples[0], conflicting_tuples[1])
                conflict_data, failed_data, conflict_count, _ = \
                    _parse_boot_results(conflicts,
                                        intersect_results=failed_data)

        # Update the necessary data to create the email report.
        kwargs["failed_data"] = failed_data
        kwargs["conflict_count"] = conflict_count
        kwargs["conflict_data"] = conflict_data
        kwargs["fail_count"] = fail_count - conflict_count
        kwargs["pass_count"] = total_count - fail_count - offline_count

        email_body, subject = _create_boot_email(**kwargs)
    elif fail_count == 0 and total_count > 0:
        email_body, subject = _create_boot_email(**kwargs)
    elif fail_count == 0 and total_count == 0:
        utils.LOG.warn(
            "Nothing found for '%s-%s': no email report sent", job, kernel)

    return email_body, subject


def _parse_job_results(results):
    """Parse the job results from the database creating a new data structure.

    This is done to provide a simpler data structure to create the email
    body.


    :param results: The job results to parse.
    :type results: `pymongo.cursor.Cursor` or a list of dict
    :return A tuple with the parsed data as dictionary.
    """
    parsed_data = None

    for result in results:
        res_get = result.get

        git_commit = res_get(models.GIT_COMMIT_KEY)
        git_url = res_get(models.GIT_URL_KEY)
        git_branch = res_get(models.GIT_BRANCH_KEY)

        parsed_data = {
            models.GIT_COMMIT_KEY: git_commit,
            models.GIT_URL_KEY: git_url,
            models.GIT_BRANCH_KEY: git_branch
        }

    return parsed_data


def _get_unique_data(results):
    """Get a dictionary with the unique values in the results.

    :param results: The `Cursor` to analyze.
    :type results: pymongo.cursor.Cursor
    :return A dictionary with the unique data found in the results.
    """
    unique_data = {}

    if isinstance(results, pymongo.cursor.Cursor):
        unique_data = {
            models.ARCHITECTURE_KEY: results.distinct(models.ARCHITECTURE_KEY),
            models.BOARD_KEY: results.distinct(models.BOARD_KEY),
            models.DEFCONFIG_FULL_KEY: results.distinct(
                models.DEFCONFIG_FULL_KEY),
            models.MACH_KEY: results.distinct(models.MACH_KEY)
        }
    return unique_data


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
    parsed_get = parsed_data.get
    result_struct = None
    unique_data = None
    intersections = 0

    if get_unique:
        unique_data = _get_unique_data(results)

    for result in results:
        res_get = result.get

        lab_name = res_get(models.LAB_NAME_KEY)
        board = res_get(models.BOARD_KEY)
        arch = res_get(models.ARCHITECTURE_KEY)
        defconfig = res_get(models.DEFCONFIG_FULL_KEY)
        status = res_get(models.STATUS_KEY)

        result_struct = {
            arch: {
                defconfig: {
                    board: {
                        lab_name: status
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
                    if intersect_results[arch][defconfig].get(board, None):
                        intersections += 1
                        del intersect_results[arch][defconfig][board]
                        # Clean up also the remainder of the data structure so
                        # that we really have cleaned up data.
                        if not intersect_results[arch][defconfig]:
                            del intersect_results[arch][defconfig]
                        if not intersect_results[arch]:
                            del intersect_results[arch]

        if arch in parsed_data.viewkeys():
            if defconfig in parsed_get(arch).viewkeys():
                if board in parsed_get(arch)[defconfig].viewkeys():
                    parsed_get(arch)[defconfig][board][lab_name] = \
                        result_struct[arch][defconfig][board][lab_name]
                else:
                    parsed_get(arch)[defconfig][board] = \
                        result_struct[arch][defconfig][board]
            else:
                parsed_get(arch)[defconfig] = result_struct[arch][defconfig]
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
          They have the same `board`, `arch` and `defconfig_full` values

        :param f_g: The `get` function for the `failed` result.
        :type f_g: function
        :param p_g: The `get` function for the `passed` result.
        :return True or False.
        """
        is_valid = False
        if all([
                f_g(models.ID_KEY) != p_g(models.ID_KEY),
                f_g(models.LAB_NAME_KEY) != p_g(models.LAB_NAME_KEY),
                f_g(models.BOARD_KEY) == p_g(models.BOARD_KEY),
                f_g(models.ARCHITECTURE_KEY) == p_g(models.ARCHITECTURE_KEY),
                f_g(models.DEFCONFIG_FULL_KEY) ==
                p_g(models.DEFCONFIG_FULL_KEY)]):
            is_valid = True
        return is_valid

    if _is_valid_pair(fail_get, pass_get):
        if fail_get(models.STATUS_KEY) != pass_get(models.STATUS_KEY):
            conflict = failed, passed

    return conflict


def _count_unique(to_count):
    """Count the number of values in a list.

    Traverse the list and consider only the valid values (non-None).

    :param to_count: The list to count.
    :type to_count: list
    :return The number of element in the list.
    """
    total = 0
    if isinstance(to_count, (types.ListType, types.TupleType)):
        filtered_list = None
        filtered_list = [x for x in to_count if x is not None]
        total = len(filtered_list)
    return total


# pylint: disable=too-many-arguments
def _create_boot_email(**kwargs):
    """Parse the results and create the email text body to send.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param git_commit: The git commit.
    :type git_commit: str
    :param git_url: The git url.
    :type git_url: str
    :param git_branch: The git branch.
    :type git_branch: str
    :param lab_name: The name of the lab.
    :type lab_name: str
    :param failed_data: The parsed failed results.
    :type failed_data: dict
    :param fail_count: The total number of failed results.
    :type fail_count: int
    :param offline_data: The parsed offline results.
    :type offline_data: dict
    :param offline_count: The total number of offline results.
    :type offline_count: int
    :param total_count: The total number of results.
    :type total_count: int
    :param total_unique_data: The unique values data structure.
    :type total_unique_data: dictionary
    :param pass_count: The total number of passed results.
    :type pass_count: int
    :param conflict_data: The parsed conflicting results.
    :type conflict_data: dict
    :param conflict_count: The number of conflicting results.
    :type conflict_count: int
    :param base_url: The base URL to build the dashboard links.
    :type base_url: string
    :param boot_url: The base URL for the boot section of the dashboard.
    :type boot_url: string
    :param build_url: The base URL for the build section of the dashboard.
    :type build_url: string
    :param git_branch: The name of the branch.
    :type git_branch: string
    :param git_commit: The git commit SHA.
    :type git_commit: string
    :param git_url: The URL to the git repository
    :type git_url: string
    :param info_email: The email address for the footer note.
    :type info_email: string
    :return A tuple with the email body and subject as strings.
    """
    k_get = kwargs.get
    total_unique_data = k_get("total_unique_data", None)
    info_email = k_get("info_email", None)

    # We use io and strings must be unicode.
    email_body = u""
    subject_str = _get_boot_subject_string(**kwargs)

    tested_one = _(u"Tested: %s\n")
    tested_two = _(u"Tested: %s, %s\n")

    tested_string = None
    if total_unique_data:
        unique_boards = _count_unique(
            total_unique_data.get(models.BOARD_KEY, None))
        unique_socs = _count_unique(
            total_unique_data.get(models.MACH_KEY, None))

        kwargs["unique_boards"] = unique_boards
        kwargs["unique_socs"] = unique_socs

        boards_str = _p(
            u"%(unique_boards)d unique board",
            u"%(unique_boards)d unique boards",
            unique_boards
        )
        soc_str = _p(
            u"%(unique_socs)d SoC family",
            u"%(unique_socs)d SoC families",
            unique_socs
        )

        if all([unique_boards > 0, unique_socs > 0]):
            tested_string = tested_two % (boards_str, soc_str)
        elif unique_boards > 0:
            tested_string = tested_one % boards_str
        elif unique_socs > 0:
            tested_string = tested_one % soc_str

        if tested_string:
            tested_string = tested_string % kwargs

    boot_summary_url = u"%(boot_url)s/%(job)s/kernel/%(kernel)s/" % kwargs
    build_summary_url = u"%(build_url)s/%(job)s/kernel/%(kernel)s/" % kwargs

    tree = _(u"Tree: %(job)s\n") % kwargs
    branch = _(u"Branch: %(git_branch)s\n") % kwargs
    git_describe = _(u"Git Describe: %(kernel)s\n") % kwargs
    git_commit = _(u"Git Commit: %(git_commit)s\n") % kwargs
    git_url = _(u"Git URL: %(git_url)s\n") % kwargs

    with io.StringIO() as m_string:
        m_string.write(subject_str)
        m_string.write(u"\n")
        m_string.write(u"\n")
        m_string.write(
            _(u"Full Boot Summary: %s\n") % boot_summary_url)
        m_string.write(
            _(u"Full Build Summary: %s\n") % build_summary_url)
        m_string.write(u"\n")
        m_string.write(tree)
        m_string.write(branch)
        m_string.write(git_describe)
        m_string.write(git_commit)
        m_string.write(git_url)

        if tested_string:
            m_string.write(tested_string)

        _parse_and_write_results(m_string, **kwargs)

        if info_email:
            m_string.write(u"\n")
            m_string.write(u"---\n")
            m_string.write(_(u"For more info write to <%s>") % info_email)

        email_body = m_string.getvalue()

    return email_body, subject_str


def _get_boot_subject_string(**kwargs):
    """Create the email subject line.

    This is used to created the custom email report line based on the number
    of values we have.

    :param total_count: The total number of boot reports.
    :type total_count: integer
    :param fail_count: The number of failed boot reports.
    :type fail_count: integer
    :param offline_count: The number of offline boards.
    :type offline_count: integer
    :param conflict_count: The number of boot reports in conflict.
    :type conflict_count: integer
    :param lab_name: The name of the lab.
    :type lab_name: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    """
    k_get = kwargs.get
    lab_name = k_get("lab_name", None)
    total_count = k_get("total_count", 0)
    conflict_count = k_get("conflict_count", 0)
    fail_count = k_get("fail_count", 0)
    offline_count = k_get("offline_count", 0)

    subject_str = u""
    base_subject = _(u"%(job)s boot")
    total_boots = _p(
        u"%(total_count)d boot", u"%(total_count)d boots", total_count)
    passed_boots = _(u"%(pass_count)d passed")
    failed_boots = _(u"%(fail_count)d failed")
    conflict_boots = _p(
        u"%(conflict_count)d conflict",
        u"%(conflict_count)d conflicts",
        conflict_count
    )
    offline_boots = _(u"%(offline_count)d offline")
    kernel_name = _(u"(%(kernel)s)")
    lab_name_str = _(u"%(lab_name)s")

    subject_substitutions = {
        "boot_name": base_subject,
        "total_boots": total_boots,
        "passed_boots": passed_boots,
        "failed_boots": failed_boots,
        "conflict_boots": conflict_boots,
        "offline_boots": offline_boots,
        "kernel_name": kernel_name,
        "lab_description": lab_name_str
    }

    subject_all_pass = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s %(kernel_name)s")
    subject_all_pass_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s %(kernel_name)s "
        "- %(lab_description)s")

    subject_pass_with_offline = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(offline_boots)s %(kernel_name)s")
    subject_pass_with_offline_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(offline_boots)s %(kernel_name)s - %(lab_description)s")

    subject_pass_with_conflict = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(conflict_boots)s %(kernel_name)s")
    subject_pass_with_conflict_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(conflict_boots)s %(kernel_name)s - %(lab_description)s")

    subject_only_fail = _(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s %(kernel_name)s")
    subject_only_fail_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s %(kernel_name)s "
        "- %(lab_description)s")

    subject_with_fail = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(failed_boots)s %(kernel_name)s")
    subject_with_fail_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(failed_boots)s %(kernel_name)s - %(lab_description)s")

    subject_with_fail_and_conflict = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, %(failed_boots)s "
        "with %(conflict_boots)s %(kernel_name)s")
    subject_with_fail_and_conflict_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, %(failed_boots)s "
        "with %(conflict_boots)s %(kernel_name)s - %(lab_description)s")

    subject_with_fail_and_offline = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, %(failed_boots)s "
        "with %(offline_boots)s %(kernel_name)s")
    subject_with_fail_and_offline_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, %(failed_boots)s "
        "with %(offline_boots)s %(kernel_name)s - %(lab_description)s")

    all_subject = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(failed_boots)s with %(conflict_boots)s, %(offline_boots)s "
        "%(kernel_name)s")
    all_subject_with_lab = _(
        u"%(boot_name)s: %(total_boots)s: %(passed_boots)s, "
        "%(failed_boots)s with %(conflict_boots)s, %(offline_boots)s "
        "%(kernel_name)s - %(lab_description)s")

    if all([fail_count == 0, offline_count == 0, conflict_count == 0]):
        # All is good!
        if lab_name:
            subject_str = subject_all_pass_with_lab
        else:
            subject_str = subject_all_pass
    elif all([fail_count == 0, offline_count == 0, conflict_count > 0]):
        if lab_name:
            subject_str = subject_pass_with_conflict_with_lab
        else:
            subject_str = subject_pass_with_conflict
    elif all([fail_count == 0, offline_count > 0, conflict_count == 0]):
        # We only have offline boards.
        if lab_name:
            subject_str = subject_pass_with_offline_with_lab
        else:
            subject_str = subject_pass_with_offline
    elif all([
            fail_count > 0, offline_count == 0, conflict_count == 0,
            fail_count == total_count]):
        # We only have failed data.
        if lab_name:
            subject_str = subject_only_fail_with_lab
        else:
            subject_str = subject_only_fail
    elif all([
            fail_count > 0, offline_count == 0, conflict_count == 0,
            fail_count != total_count]):
        # We have some failed boots.
        if lab_name:
            subject_str = subject_with_fail_with_lab
        else:
            subject_str = subject_with_fail
    elif all([
            fail_count > 0, offline_count > 0, conflict_count == 0,
            fail_count != total_count]):
        # We have failed and offline boots.
        if lab_name:
            subject_str = subject_with_fail_and_offline_with_lab
        else:
            subject_str = subject_with_fail_and_offline
    elif all([
            fail_count > 0, offline_count == 0, conflict_count > 0,
            fail_count != total_count]):
        # We have failed on conflicting boots.
        if lab_name:
            subject_str = subject_with_fail_and_conflict_with_lab
        else:
            subject_str = subject_with_fail_and_conflict
    elif all([
            fail_count > 0, offline_count > 0, conflict_count > 0,
            fail_count != total_count]):
        # We have everything, failed, offline and conflicting.
        if lab_name:
            subject_str = all_subject_with_lab
        else:
            subject_str = all_subject

    # Perform all the normal placeholder substitutions.
    subject_str = subject_str % subject_substitutions
    # Now fill in the values.
    subject_str = subject_str % kwargs

    return subject_str


def _parse_and_write_results(m_string, **kwargs):
    """Parse failed and conflicting results and create the email body.

    :param m_string: The StringIO object where to write.
    :param failed_data: The parsed failed results.
    :type failed_data: dict
    :param offline_data: The parsed offline results.
    :type offline_data: dict
    :param conflict_data: The parsed conflicting results.
    :type conflict_data: dict
    :param args: A dictionary with values for string formatting.
    :type args: dict
    """
    k_get = kwargs.get

    offline_data = k_get("offline_data", None)
    failed_data = k_get("failed_data", None)
    conflict_data = k_get("conflict_data", None)
    fail_count = k_get("fail_count", 0)
    conflict_count = k_get("conflict_count", 0)

    def _traverse_data_struct(data, m_string):
        """Traverse the data structure and write it to file.

        :param data: The data structure to parse.
        :type data: dict
        :param m_string: The open file where to write.
        :type m_string: io.StringIO
        """
        d_get = data.get

        for arch in data.viewkeys():
            m_string.write(u"\n")
            m_string.write(
                _(u"%s:\n") % arch
            )

            for defconfig in d_get(arch).viewkeys():
                m_string.write(u"\n")
                m_string.write(
                    _(u"    %s:\n") % defconfig
                )
                def_get = d_get(arch)[defconfig].get

                for board in d_get(arch)[defconfig].viewkeys():
                    m_string.write(
                        _(u"        %s:\n") % board
                    )

                    for lab in def_get(board).viewkeys():
                        m_string.write(
                            _(u"            %s: %s\n") %
                            (lab, def_get(board)[lab])
                        )

    if offline_data:
        m_string.write(_(u"\nOffline Platforms:\n"))
        _traverse_data_struct(offline_data, m_string)

    if failed_data:
        boot_failure_url = u"%(base_url)s/boot/?%(kernel)s&fail" % kwargs

        m_string.write(u"\n")
        m_string.write(
            _p(
                u"Boot Failure Detected: %(boot_failure_url)s\n",
                u"Boot Failures Detected: %(boot_failure_url)s\n",
                fail_count
            ) % {"boot_failure_url": boot_failure_url}

        )
        _traverse_data_struct(failed_data, m_string)

    if conflict_data:
        conflict_comment = _(
            u"(These likely are not failures as other labs are reporting "
            "PASS. Please review.)")
        m_string.write(u"\n")
        m_string.write(
            _p(
                u"Conflicting Boot Failure Detected: %(conflict_comment)s\n",
                u"Conflicting Boot Failures Detected: %(conflict_comment)s\n",
                conflict_count
            ) % {"conflict_comment": conflict_comment}
        )
        _traverse_data_struct(conflict_data, m_string)
