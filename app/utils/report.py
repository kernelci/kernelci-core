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

import io
import itertools
import pymongo

import models
import models.report as mreport
import utils
import utils.db

DEFAULT_BASE_URL = u"http://kernelci.org"
DEFAULT_BOOT_URL = u"http://kernelci.org/boot/all/job"
DEFAULT_BUILD_URL = u"http://kernelci.org/build"

BOOT_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.BOARD_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.LAB_NAME_KEY,
    models.STATUS_KEY
]

BOOT_SEARCH_SORT = [
    (models.ARCHITECTURE_KEY, pymongo.ASCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING),
    (models.BOARD_KEY, pymongo.ASCENDING)
]


# pylint: disable=too-many-arguments
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
def create_boot_report(job, kernel, db_options):
    """Create the boot report email to be sent.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A tuple with the email body and subject as strings or None.
    """
    email_body = None
    subject = None

    database = utils.db.get_db_connection(db_options)

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
    }

    _, total_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=[models.ID_KEY])

    spec[models.STATUS_KEY] = {"$ne": models.PASS_STATUS}
    fail_results, fail_count = utils.db.find_and_count(
        database[models.BOOT_COLLECTION],
        0,
        0,
        spec=spec,
        fields=BOOT_SEARCH_FIELDS,
        sort=BOOT_SEARCH_SORT)

    if fail_count > 0:
        failed_data, unique_data = _parse_results(
            fail_results.clone(), get_unique=True)

        # Copy the failed results here. The mongodb Cursor, for some
        # reasons gets overwritten.
        fail_results = [x for x in fail_results.clone()]

        conflict_data = None
        if fail_count != total_count:
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
                conflict_data, _ = _parse_results(conflicts)

        email_body, subject = _create_boot_email(
            job, kernel, failed_data, fail_count, total_count, conflict_data)
    else:
        utils.LOG.warn(
            "No results found for job '%s' and kernel '%s': "
            "email report not created",
            job, kernel)

    return email_body, subject


def _parse_results(results, get_unique=False):
    """Parse the results from the database creating a new data structure.

    This is done to provide a simpler data structure to create the email
    body.

    If `get_unique` is True, it will return also a dictionary with unique
    values found in the passed `results` for `arch`, `board` and
    `defconfig_full` keys.

    :param results: The results to parse.
    :type results: `pymongo.cursor.Cursor` or a list of dict
    :param get_unique: Return the unique values in the data structure. Default
    to False.
    :type get_unique: bool
    :return A tuple with the parsed data as dictionary, and the unique data or
    None.
    """
    parsed_data = {}
    parsed_get = parsed_data.get
    result_struct = None
    unique_data = None

    if get_unique:
        unique_data = {
            models.ARCHITECTURE_KEY: results.distinct(models.ARCHITECTURE_KEY),
            models.BOARD_KEY: results.distinct(models.BOARD_KEY),
            models.DEFCONFIG_FULL_KEY: results.distinct(
                models.DEFCONFIG_FULL_KEY)
        }

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

    return parsed_data, unique_data


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


# pylint: disable=too-many-arguments
def _create_boot_email(
        job, kernel, failed_data, fail_count, total_count, conflict_data):
    """Parse the results and create the email text body to send.

    :param job: The name of the job.
    :type job: str
    :param  kernel: The name of the kernel.
    :type kernel: str
    :param failed_data: The parsed failed results.
    :type reduce: dict
    :param fail_count: The total number of failed results.
    :type fail_count: int
    :param total_count: The total number of results.
    :type total_count: int
    :param conflict_data: The parsed conflicting results.
    :type conflict_data: dict
    :return A tuple with the email body and subject as strings.
    """
    args = {
        "job": job,
        "total_results": total_count,
        "passed": total_count - fail_count,
        "failed": fail_count,
        "kernel": kernel,
        "base_url": DEFAULT_BASE_URL,
        "build_url": DEFAULT_BUILD_URL,
        "boot_url": DEFAULT_BOOT_URL
    }

    email_body = u""
    subject = (
        u"%(job)s boot: %(total_results)d boots: "
        "%(passed)d passed, %(failed)d failed (%(kernel)s)" % args
    )

    with io.StringIO() as m_string:
        m_string.write(
            u"Full Build Summary: %(build_url)s/%(job)s/kernel/%(kernel)s/\n" %
            args
        )
        m_string.write(
            u"Full Boot Summary: %(boot_url)s/%(job)s/kernel/%(kernel)s/\n" %
            args
        )
        m_string.write(u"\n")
        m_string.write(
            u"Tree/Branch: %(job)s\nGit Describe: %(kernel)s\n" % args
        )
        _parse_and_write_results(failed_data, conflict_data, args, m_string)
        email_body = m_string.getvalue()

    return email_body, subject


def _parse_and_write_results(failed_data, conflict_data, args, m_string):
    """Parse failed and conflicting results and create the email body.

    :param failed_data: The parsed failed results.
    :type failed_data: dict
    :param conflict_data: The parsed conflicting results.
    :type conflict_data: dict
    :param args: A dictionary with values for string formatting.
    :type args: dict
    :param m_string: The StriongIO object where to write.
    """

    def _traverse_data_struct(data, m_string):
        """Traverse the data structure and write it to file.

        :param data: The data structure to parse.
        :type data: dict
        :param m_string: The open file where to write.
        :type m_string: io.StringIO
        """
        d_get = data.get

        for arch in data.viewkeys():
            m_string.write(
                u"\n%s:\n" % arch
            )

            for defconfig in d_get(arch).viewkeys():
                m_string.write(
                    u"\n    %s:\n" % defconfig
                )
                def_get = d_get(arch)[defconfig].get

                for board in d_get(arch)[defconfig].viewkeys():
                    m_string.write(
                        u"        %s:\n" % board
                    )

                    for lab in def_get(board).viewkeys():
                        m_string.write(
                            u"            %s: %s\n" %
                            (lab, def_get(board)[lab])
                        )

    if failed_data:
        m_string.write(
            u"\nFailed Boot Results: %(boot_url)s/?%(kernel)s&fail\n" % args
        )
        _traverse_data_struct(failed_data, m_string)

    if conflict_data:
        m_string.write(u"\nConflicting Boot Results: (Review needed)\n")
        _traverse_data_struct(conflict_data, m_string)
