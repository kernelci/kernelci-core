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

import gettext
import io
import itertools
import pymongo

import models
import utils.db
import utils.report.common as rcommon

# Register the translation domain and fallback safely, at the moment we do
# not care if we have translations or not, we just use gettext to exploit its
# plural forms capabilities. We mark the email string as translatable though
# so we might give that feature in the future.
L10N = gettext.translation(models.I18N_DOMAIN, fallback=True)
# Register normal Unicode gettext.
G_ = L10N.ugettext
# Register plural forms Unicode gettext.
P_ = L10N.ungettext


BOOT_SEARCH_SORT = [
    (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
    (models.BOARD_KEY, pymongo.ASCENDING)
]

BOOT_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.LAB_NAME_KEY,
    models.MACH_KEY,
    models.STATUS_KEY
]


# pylint: disable=too-many-locals
# pylint: disable=star-args
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

    total_count, total_unique_data = rcommon.get_total_results(
        job,
        kernel,
        models.BOOT_COLLECTION,
        db_options,
        lab_name=lab_name
    )

    total_builds, _ = rcommon.get_total_results(
        job,
        kernel,
        models.DEFCONFIG_COLLECTION,
        db_options
    )

    git_commit, git_url, git_branch = rcommon.get_git_data(
        job, kernel, db_options)

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.STATUS_KEY: models.OFFLINE_STATUS
    }

    if lab_name is not None:
        spec[models.LAB_NAME_KEY] = lab_name

    database = utils.db.get_db_connection(db_options)
    offline_results, offline_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT)

    # MongoDB cursor gets overwritten somehow by the next query. Extract the
    # data before this happens.
    offline_data = None
    if offline_count > 0:
        offline_data, _, _, _ = _parse_boot_results(offline_results.clone())

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
        "base_url": rcommon.DEFAULT_BASE_URL,
        "boot_url": rcommon.DEFAULT_BOOT_URL,
        "build_url": rcommon.DEFAULT_BUILD_URL,
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
        "total_builds": total_builds,
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

                # Make sure we do not have an empty list here after filtering.
                if conflicting_tuples:
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
    parsed_get = parsed_data.get
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
    :param total_builds: The total number of defconfig built.
    :type total_builds: int
    :param base_url: The base URL to build the dashboard links.
    :type base_url: string
    :param boot_url: The base URL for the boot section of the dashboard.
    :type boot_url: string
    :param build_url: The base URL for the build section of the dashboard.
    :type build_url: string
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

    tested_one = G_(u"Tested: %s\n")
    tested_two = G_(u"Tested: %s, %s\n")
    tested_three = G_(u"Tested: %s, %s, %s\n")

    tested_string = None
    if total_unique_data:
        unique_boards = rcommon.count_unique(
            total_unique_data.get(models.BOARD_KEY, None))
        unique_socs = rcommon.count_unique(
            total_unique_data.get(models.MACH_KEY, None))
        unique_builds = rcommon.count_unique(
            total_unique_data[models.DEFCONFIG_FULL_KEY])

        kwargs["unique_boards"] = unique_boards
        kwargs["unique_socs"] = unique_socs
        kwargs["unique_builds"] = unique_builds

        boards_str = P_(
            u"%(unique_boards)d unique board",
            u"%(unique_boards)d unique boards",
            unique_boards
        )
        soc_str = P_(
            u"%(unique_socs)d SoC family",
            u"%(unique_socs)d SoC families",
            unique_socs
        )
        builds_str = P_(
            u"%(unique_builds)s build out of %(total_builds)s",
            u"%(unique_builds)s builds out of %(total_builds)s",
            unique_builds
        )

        if all([unique_boards > 0, unique_socs > 0, unique_builds > 0]):
            tested_string = tested_three % (boards_str, soc_str, builds_str)
        elif all([unique_boards > 0, unique_socs > 0, unique_builds == 0]):
            tested_string = tested_two % (boards_str, soc_str)
        elif all([unique_boards > 0, unique_socs == 0, unique_builds > 0]):
            tested_string = tested_two % (boards_str, builds_str)
        elif all([unique_boards == 0, unique_socs > 0, unique_builds > 0]):
            tested_string = tested_two % (soc_str, builds_str)
        elif all([unique_boards > 0, unique_socs == 0, unique_builds == 0]):
            tested_string = tested_one % boards_str
        elif all([unique_boards == 0, unique_socs > 0, unique_builds == 0]):
            tested_string = tested_one % soc_str
        elif all([unique_boards == 0, unique_socs == 0, unique_builds > 0]):
            tested_string = tested_one % builds_str

        if tested_string:
            tested_string = tested_string % kwargs

    boot_summary_url = u"%(boot_url)s/%(job)s/kernel/%(kernel)s/" % kwargs
    build_summary_url = u"%(build_url)s/%(job)s/kernel/%(kernel)s/" % kwargs

    tree = G_(u"Tree: %(job)s\n") % kwargs
    branch = G_(u"Branch: %(git_branch)s\n") % kwargs
    git_describe = G_(u"Git Describe: %(kernel)s\n") % kwargs
    git_commit = G_(u"Git Commit: %(git_commit)s\n") % kwargs
    git_url = G_(u"Git URL: %(git_url)s\n") % kwargs

    with io.StringIO() as m_string:
        m_string.write(subject_str)
        m_string.write(u"\n")
        m_string.write(u"\n")
        m_string.write(
            G_(u"Full Boot Summary: %s\n") % boot_summary_url)
        m_string.write(
            G_(u"Full Build Summary: %s\n") % build_summary_url)
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
            m_string.write(G_(u"For more info write to <%s>") % info_email)

        email_body = m_string.getvalue()

    return email_body, subject_str


# pylint: disable=invalid-name
def _get_boot_subject_string(**kwargs):
    """Create the boot email subject line.

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
    :param pass_count: The number of successful boot reports.
    :type pass_count: integer
    :param lab_name: The name of the lab.
    :type lab_name: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :return The subject string.
    """
    k_get = kwargs.get
    lab_name = k_get("lab_name", None)
    total_count = k_get("total_count", 0)
    conflict_count = k_get("conflict_count", 0)
    fail_count = k_get("fail_count", 0)
    offline_count = k_get("offline_count", 0)

    subject_str = u""
    base_subject = G_(u"%(job)s boot")
    total_boots = P_(
        u"%(total_count)d boot", u"%(total_count)d boots", total_count)
    passed_boots = G_(u"%(pass_count)d passed")
    failed_boots = G_(u"%(fail_count)d failed")
    conflict_boots = P_(
        u"%(conflict_count)d conflict",
        u"%(conflict_count)d conflicts",
        conflict_count
    )
    offline_boots = G_(u"%(offline_count)d offline")
    kernel_name = G_(u"(%(kernel)s)")
    lab_name_str = G_(u"%(lab_name)s")

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

    subject_all_pass = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, "
        "%(passed_boots)s %(kernel_name)s")
    subject_all_pass_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s:  %(failed_boots)s, "
        "%(passed_boots)s %(kernel_name)s - %(lab_description)s")

    subject_pass_with_offline = G_(
        u"%(boot_name)s: %(total_boots)s:  %(failed_boots)s, "
        "%(passed_boots)s, %(offline_boots)s %(kernel_name)s")
    subject_pass_with_offline_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s:  %(failed_boots)s, "
        "%(passed_boots)s, %(offline_boots)s %(kernel_name)s "
        "- %(lab_description)s"
    )

    subject_pass_with_conflict = G_(
        u"%(boot_name)s: %(total_boots)s:  %(failed_boots)s, "
        "%(passed_boots)s, %(conflict_boots)s %(kernel_name)s")
    subject_pass_with_conflict_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, "
        "%(passed_boots)s, %(conflict_boots)s %(kernel_name)s "
        "- %(lab_description)s"
    )

    subject_only_fail = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s %(kernel_name)s")
    subject_only_fail_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s %(kernel_name)s "
        "- %(lab_description)s")

    subject_with_fail = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "%(kernel_name)s")
    subject_with_fail_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "%(kernel_name)s - %(lab_description)s")

    subject_with_fail_and_conflict = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(conflict_boots)s %(kernel_name)s")
    subject_with_fail_and_conflict_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(conflict_boots)s %(kernel_name)s - %(lab_description)s")

    subject_with_fail_and_offline = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(offline_boots)s %(kernel_name)s")
    subject_with_fail_and_offline_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(offline_boots)s %(kernel_name)s - %(lab_description)s")

    all_subject = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(conflict_boots)s, %(offline_boots)s %(kernel_name)s")
    all_subject_with_lab = G_(
        u"%(boot_name)s: %(total_boots)s: %(failed_boots)s, %(passed_boots)s "
        "with %(conflict_boots)s, %(offline_boots)s %(kernel_name)s "
        "- %(lab_description)s"
    )

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

    def _traverse_data_struct(
            data, m_string, is_conflict=False, is_offline=False):
        """Traverse the data structure and write it to file.

        :param data: The data structure to parse.
        :type data: dict
        :param m_string: The open file where to write.
        :type m_string: io.StringIO
        :param is_conflict: If the data passed has to be considered a conflict
        aggregation.
        :type is_conflict: bool
        :param is_offline: If the data passed has to be considered an offline
        aggregation.
        :type is_offline: bool
        """
        d_get = data.get

        for arch in data.viewkeys():
            m_string.write(u"\n")
            m_string.write(G_(u"%s:\n") % arch)

            # Force defconfs to be sorted.
            defconfs = list(d_get(arch).viewkeys())
            defconfs.sort()

            for defconfig in defconfs:
                m_string.write(u"\n")
                m_string.write(G_(u"    %s:\n") % defconfig)
                def_get = d_get(arch)[defconfig].get

                # Force boards to be sorted.
                boards = list(d_get(arch)[defconfig].viewkeys())
                boards.sort()

                if is_conflict:
                    for board in boards:
                        m_string.write(G_(u"        %s:\n") % board)

                        for lab in def_get(board).viewkeys():
                            m_string.write(
                                G_(u"            %s: %s\n") %
                                (lab, def_get(board)[lab]))
                else:
                    # Not a conflict data structure, we show only the count of
                    # the failed labs, not which one failed.
                    for board in boards:
                        lab_count = 0
                        for lab in def_get(board).viewkeys():
                            lab_count += 1

                        if is_offline:
                            lab_count_str = (
                                P_(
                                    "%d offline lab",
                                    "%d offline labs", lab_count
                                ) % lab_count)
                        else:
                            lab_count_str = (
                                P_(
                                    "%d failed lab",
                                    "%d failed labs", lab_count
                                ) % lab_count)
                        m_string.write(
                            G_(u"        %s: %s\n") % (board, lab_count_str))

    if failed_data:
        boot_failure_url = u"%(base_url)s/boot/?%(kernel)s&fail" % kwargs

        m_string.write(u"\n")
        m_string.write(
            P_(
                u"Boot Failure Detected: %(boot_failure_url)s\n",
                u"Boot Failures Detected: %(boot_failure_url)s\n",
                fail_count
            ) % {"boot_failure_url": boot_failure_url}

        )
        _traverse_data_struct(failed_data, m_string)

    if offline_data:
        m_string.write(G_(u"\nOffline Platforms:\n"))
        _traverse_data_struct(offline_data, m_string, is_offline=True)

    if conflict_data:
        conflict_comment = G_(
            u"(These likely are not failures as other labs are reporting "
            "PASS. Please review.)")
        m_string.write(u"\n")
        m_string.write(
            P_(
                u"Conflicting Boot Failure Detected: %(conflict_comment)s\n",
                u"Conflicting Boot Failures Detected: %(conflict_comment)s\n",
                conflict_count
            ) % {"conflict_comment": conflict_comment}
        )
        _traverse_data_struct(conflict_data, m_string, is_conflict=True)
