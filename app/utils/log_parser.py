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

"""Extract and save build log errors."""

try:
    import simplejson as json
except ImportError:
    import json

try:
    from os import scandir
except ImportError:
    from scandir import scandir

import bson
import datetime
import io
import itertools
import os
import re

import models
import models.defconfig as mdefconfig
import models.error_log as merrl
import models.error_summary as mesumm
import utils
import utils.build
import utils.errors


ERROR_PATTERN_1 = re.compile("[Ee]rror:")
ERROR_PATTERN_2 = re.compile("^ERROR")
WARNING_PATTERN = re.compile("warning:?", re.IGNORECASE)
MISMATCH_PATTERN = re.compile("Section mismatch", re.IGNORECASE)

# Regex pattern to exclude.
NO_WARNING_PATTERN_1 = re.compile(
    # pylint: disable=fixme
    "TODO: return_address should use unwind tables", re.IGNORECASE)
# pylint: enable=fixme
NO_WARNING_PATTERN_2 = re.compile(
    "NPTL on non MMU needs fixing", re.IGNORECASE)
NO_WARNING_PATTERN_3 = re.compile(
    "Sparse checking disabled for this file", re.IGNORECASE)

EXCLUDE_PATTERNS = [
    NO_WARNING_PATTERN_1,
    NO_WARNING_PATTERN_2,
    NO_WARNING_PATTERN_3,
]

ERROR_PATTERNS = [
    ERROR_PATTERN_1,
    ERROR_PATTERN_2
]

ERR_ADD = utils.errors.add_error


def _dict_to_list(data):
    """Transform a dictionary into a list of tuples.

    :param data: The dictionary to transform.
    :return A list of tuples.
    """
    tupl = zip(data.values(), data.keys())
    tupl.sort()
    tupl.reverse()
    return tupl


def count_lines(error_lines, warning_lines, mismatch_lines):
    """Count the available lines for errors, warnings and mismatches.

    :param error_lines: The error lines.
    :param warning_lines: The warning lines.
    :param mismatch_lines: The mismatched line.
    """
    errors_all = {}
    warnings_all = {}
    mismatches_all = {}

    err_default = errors_all.setdefault
    warn_default = warnings_all.setdefault
    mism_default = mismatches_all.setdefault

    # Store what we found for each defconfig in the db, only if we have
    # something.
    if any([error_lines, warning_lines, mismatch_lines]):
        for err, warn, mism in itertools.izip_longest(
                error_lines, warning_lines, mismatch_lines):
            if err:
                errors_all[err] = err_default(err, 0) + 1
            if warn:
                warnings_all[warn] = warn_default(warn, 0) + 1
            if mism:
                mismatches_all[mism] = mism_default(mism, 0) + 1

    return errors_all, warnings_all, mismatches_all


# pylint: disable=too-many-arguments
def _save_summary(errors,
                  warnings, mismatches, job_id, job, kernel, db_options):
    """Save the summary for errors/warnings/mismatches found."""
    ret_val = 200
    if any([errors, warnings, mismatches]):
        error_summary = mesumm.ErrorSummaryDocument(job_id, "1.0")
        error_summary.created_on = datetime.datetime.now(
            tz=bson.tz_util.utc)
        error_summary.job = job
        error_summary.kernel = kernel

        # Store the summary as lists of 2-tuple values.
        error_summary.errors = _dict_to_list(errors)
        error_summary.mismatches = _dict_to_list(mismatches)
        error_summary.warnings = _dict_to_list(warnings)

        database = utils.db.get_db_connection(db_options)
        prev_spec = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.NAME_KEY: job_id
        }
        prev_doc = utils.db.find_one2(
            database[models.ERRORS_SUMMARY_COLLECTION],
            prev_spec, fields=[models.ID_KEY]
        )

        manipulate = True
        if prev_doc:
            manipulate = False
            error_summary.id = prev_doc[models.ID_KEY]

        ret_val, _ = utils.db.save(
            database, error_summary, manipulate=manipulate)

    return ret_val


# pylint: disable=too-many-locals
def save_defconfig_errors(
        defconfig_doc,
        job_id, error_lines, warning_lines, mismatch_lines, db_options):
    """Save the build errors found.

    Save in the database the extracted lines from the build log.

    :param job_id: The ID of the job.
    :type job_id: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :param defconfig: The defconfig value.
    :type defconfig: string
    :param defconfig_full: The full defconfig value.
    :type defconfig_full: string
    :param arch: The architecture type.
    :type arch: string
    :param build_status: The status of the build.
    :type build_status: string
    :param error_lines: The extracted error lines.
    :type error_lines: list
    :param warning_lines: The extracted warning lines.
    :type warning_lines: list
    :param mismatch_lines: The extracted mismatch lines.
    :type mismatch_lines: list
    :param db_options: The database connection options.
    :type db_options: dictionary
    :return 201 if saving has success, 500 otherwise.
    """
    defconfig_id = None
    database = utils.db.get_db_connection(db_options)
    if not defconfig_doc.id:
        spec = {
            models.JOB_ID_KEY: job_id,
            models.JOB_KEY: defconfig_doc.job,
            models.KERNEL_KEY: defconfig_doc.kernel,
            models.ARCHITECTURE_KEY: defconfig_doc.arch,
            models.DEFCONFIG_KEY: defconfig_doc.defconfig,
            models.DEFCONFIG_FULL_KEY: defconfig_doc.defconfig_full
        }

        doc = utils.db.find_one2(
            database[models.DEFCONFIG_COLLECTION],
            spec, fields=[models.ID_KEY])

        if doc:
            defconfig_id = doc[models.ID_KEY]
        else:
            error = "No defconfig ID found for %s-%s-%s (%s)"
            utils.LOG.warn(
                error,
                defconfig_doc.job,
                defconfig_doc.kernel,
                defconfig_doc.defconfig_full, defconfig_doc.arch
            )
    else:
        defconfig_id = defconfig_doc.id

    if defconfig_id:
        prev_spec = {
            models.DEFCONFIG_ID_KEY: defconfig_id
        }
    else:
        prev_spec = {
            models.JOB_KEY: defconfig_doc.job,
            models.KERNEL_KEY: defconfig_doc.kernel,
            models.ARCHITECTURE_KEY: defconfig_doc.arch,
            models.DEFCONFIG_FULL_KEY: defconfig_doc.defconfig_full,
            models.DEFCONFIG_KEY: defconfig_doc.defconfig,
            models.STATUS_KEY: defconfig_doc.status
        }
    prev_doc = utils.db.find_one2(
        database[models.ERROR_LOGS_COLLECTION],
        prev_spec, fields=[models.ID_KEY])

    err_doc = merrl.ErrorLogDocument(job_id, "1.0")
    err_doc.arch = defconfig_doc.arch
    err_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    err_doc.defconfig = defconfig_doc.defconfig
    err_doc.defconfig_full = defconfig_doc.defconfig_full
    err_doc.defconfig_id = defconfig_id
    err_doc.errors = error_lines
    err_doc.errors_count = len(error_lines)
    err_doc.job = defconfig_doc.job
    err_doc.kernel = defconfig_doc.kernel
    err_doc.mismatch_lines = len(mismatch_lines)
    err_doc.mismatches = mismatch_lines
    err_doc.status = defconfig_doc.status
    err_doc.warnings = warning_lines
    err_doc.warnings_count = len(warning_lines)

    manipulate = True
    if prev_doc:
        manipulate = False
        err_doc.id = prev_doc[models.ID_KEY]

    ret_val, _ = utils.db.save(database, err_doc, manipulate=manipulate)

    return ret_val


def _save(
        defconfig_doc,
        job_id, err_lines, warn_lines, mism_lines, errors, db_options):
    """Save the found errors/warnings/mismatched lines in the db.

    Save for each defconfig the found values and update the summary data
    structures that will contain all the found errors/warnings/mismatches.

    """
    job = defconfig_doc.job
    kernel = defconfig_doc.kernel

    status = save_defconfig_errors(
        defconfig_doc, job_id, err_lines, warn_lines, mism_lines, db_options)

    if status == 500:
        err_msg = (
            "Error saving errors log document for "
            "'%s-%s-%s' (%s)" %
            (job, kernel, defconfig_doc.defconfig_full, defconfig_doc.arch)
        )
        utils.LOG.error(err_msg)
        ERR_ADD(errors, status, err_msg)

    all_errors, all_warnings, all_mismatches = count_lines(
        err_lines, warn_lines, mism_lines)

    # Once done, save the summary.
    status = _save_summary(
        all_errors,
        all_warnings, all_mismatches, job_id, job, kernel, db_options)

    if status == 500:
        error_msg = "Error saving errors summary for %s-%s (%s)"
        utils.LOG.error(error_msg, job, kernel, job_id)
        ERR_ADD(errors, status, error_msg % (job, kernel, job_id))

    return status


def _read_build_data(build_dir, job, kernel, errors):
    """Locally read the build JSON file to retrieve some values.

    Search for the correct defconfig, defconfig_full and arch values.

    :param build_dir: The directory containing the build JSON file.
    :type build_dir: string
    :return A 4-tuple: defconfig, defconfig_full, arch and build status.
    """
    build_file = os.path.join(build_dir, models.BUILD_META_JSON_FILE)
    defconfig_doc = None

    if os.path.isfile(build_file):
        build_data = None

        try:
            with io.open(build_file, "r") as read_file:
                build_data = json.load(read_file)

            defconfig_doc = utils.build.parse_build_data(
                build_data, job, kernel, errors, build_dir=build_dir)
        except IOError, ex:
            err_msg = (
                "Error reading build data file (job: %s, kernel: %s) - %s")
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg, job, kernel, build_dir)
            ERR_ADD(errors, 500, err_msg % (job, kernel, build_dir))
        except json.JSONDecodeError, ex:
            err_msg = "Error loading build data (job: %s, kernel: %s) - %s"
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg, job, kernel, build_dir)
            ERR_ADD(errors, 500, err_msg % (job, kernel, build_dir))
    else:
        error = "Missing build data file for '%s-%s' (%s)"
        utils.LOG.warn(error, job, kernel, build_dir)
        ERR_ADD(errors, 500, (error % (job, kernel, build_dir)))

    return defconfig_doc


# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def _parse_log(job, kernel, defconfig, log_file, build_dir, errors):
    """Read the build log and extract the correct strings.

    Parse the build log extracting the errors/warnings/mismatches strings
    saving new files for each of the extracted value.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param defconfig: The name of the defconfig.
    :param log_file: The file to parse.
    :param build_dir: The directory where the file is located.
    :return A status code (200 = OK, 500 = error) and
    the lines for errors, warnings and mismatches as lists.
    """
    def _clean_path(line):
        """Strip the beginning of the line if it contains a special sequence.

        :param line: The line to clean.
        :type line: string
        :return The line without the special sequence.
        """
        if line.startswith("../"):
            line = line[3:]
        return line

    status = 200

    error_lines = []
    warning_lines = []
    mismatch_lines = []

    errors_file = os.path.join(build_dir, utils.BUILD_ERRORS_FILE)
    warnings_file = os.path.join(build_dir, utils.BUILD_WARNINGS_FILE)
    mismatches_file = os.path.join(build_dir, utils.BUILD_MISMATCHES_FILE)

    if os.path.isfile(log_file):
        utils.LOG.info("Parsing build log file '%s'", log_file)

        err_append = error_lines.append
        warn_append = warning_lines.append
        mismatch_append = mismatch_lines.append

        try:
            with io.open(log_file) as read_file:
                for line in read_file:
                    has_err = has_warn = False
                    for err_pattrn in ERROR_PATTERNS:
                        if re.search(err_pattrn, line):
                            line = line.strip()
                            has_err = True
                            err_append(_clean_path(line))
                            break

                    if not has_err:
                        if re.search(WARNING_PATTERN, line):
                            for warn_pattrn in EXCLUDE_PATTERNS:
                                if re.search(warn_pattrn, line):
                                    break
                            else:
                                has_warn = True
                                line = line.strip()
                                warn_append(_clean_path(line))

                    if any([not has_err, not has_warn]):
                        if re.search(MISMATCH_PATTERN, line):
                            line = line.strip()
                            mismatch_append(_clean_path(line))
        except IOError, ex:
            err_msg = "Cannot read build log file for %s-%s-%s"
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg, job, kernel, defconfig)
            status = 500
            ERR_ADD(errors, status, err_msg % (job, kernel, defconfig))
        else:
            try:
                # TODO: count the lines here.
                if error_lines:
                    with io.open(errors_file, mode="w") as w_file:
                        for line in error_lines:
                            w_file.write(line)
                            w_file.write(u"\n")
                if warning_lines:
                    with io.open(warnings_file, mode="w") as w_file:
                        for line in warning_lines:
                            w_file.write(line)
                            w_file.write(u"\n")
                if mismatch_lines:
                    with io.open(mismatches_file, mode="w") as w_file:
                        for line in mismatch_lines:
                            w_file.write(line)
                            w_file.write(u"\n")
            except IOError, ex:
                err_msg = "Error writing to errors/warnings file for %s-%s-%s"
                utils.LOG.exception(ex)
                utils.LOG.error(err_msg, job, kernel, defconfig)
                status = 500
                ERR_ADD(errors, status, err_msg % (job, kernel, defconfig))
    else:
        utils.LOG.warn("Build dir '%s' does not have a build log" % defconfig)
        status = 500

    return status, error_lines, warning_lines, mismatch_lines


def _traverse_dir_and_parse(
        job_id, job, kernel, base_path, build_log, db_options=None):
    """Traverse the kernel directory and parse the build logs.

    :param job_id: The ID of the job.
    :type job_id: string
    :param job: The name of the job.
    :type job: string
    :param kernel: The name of the kernel.
    :type kernel: string
    :param base_path: The path on the file system where the files are stored.
    :type base_path: string
    :param build_log: The name of the build log file.
    :type build_log: string
    :param db_options: The database connection options.
    :type db_options: dictionary
    """
    if db_options is None:
        db_options = {}

    errors = {}
    status = 200

    if all([utils.valid_name(job), utils.valid_name(kernel)]):
        job_dir = os.path.join(base_path, job)
        kernel_dir = os.path.join(job_dir, kernel)

        if os.path.isdir(kernel_dir):
            for entry in scandir(kernel_dir):
                if all([entry.is_dir(), not entry.name.startswith(".")]):
                    log_file = os.path.join(entry.path, build_log)

                    defconfig_doc = _read_build_data(
                        entry.path, job, kernel, errors)

                    status, err_lines, warn_lines, mism_lines = _parse_log(
                        defconfig_doc.job,
                        defconfig_doc.kernel,
                        defconfig_doc.defconfig, log_file, entry.path, errors
                    )

                    if status == 200:
                        status = _save(
                            defconfig_doc,
                            job_id,
                            err_lines,
                            warn_lines, mism_lines, errors, db_options)
        else:
            error = "Provided values (%s,%s) do not match a directory"
            utils.LOG.error(error, job, kernel)
            status = 500
            ERR_ADD(errors, status, error % (job, kernel))
    else:
        utils.LOG.error(
            "Wrong value passed for job and/or kernel: %s - %s", job, kernel)
        status = 500
        ERR_ADD(errors, 500, "Cannot work with hidden directories")

    return status, errors


def parse_build_log(job_id,
                    json_obj,
                    db_options,
                    base_path=utils.BASE_PATH,
                    build_log=utils.BUILD_LOG_FILE):
    """Parse the build log file searching for errors and warnings.

    :param job_id: The ID of the job as saved in the database.
    :type job_id: string
    :param json_obj: The JSON object with the job and kernel name.
    :type json_obj: dictionary
    :param db_options: The database connection options.
    :type db_options: dictionary
    :param base_path: The path on the file system where the files are stored.
    :type base_path: string
    :param build_log: The name of the build log file.
    :type build_log: string
    :return A status code and a dictionary. 200 if everything is good, 500 in
    case of errors; an empty dictionary if there are no errors, otherwise the
    dictionary will contain error codes and messages lists.
    """
    status = 200
    errors = {}

    j_get = json_obj.get
    job = j_get(models.JOB_KEY)
    kernel = j_get(models.KERNEL_KEY)

    if job_id:
        status, errors = _traverse_dir_and_parse(
            job_id, job, kernel, base_path, build_log, db_options=db_options)
    else:
        status = 500
        errors[status] = ["No job ID specified, cannot continue"]

    return status, errors


def parse_single_build_log(
        build_id,
        job_id,
        db_options, base_path=utils.BASE_PATH, build_log=utils.BUILD_LOG_FILE):
    """Parse the build log file of a single build instance.

    :param build_id: The ID of the saved build.
    :param job_id: The ID of the saved job.
    :param db_options: The database connection options.
    :param base_path: The base path on the file system where data is stored.
    :param build_log: The name of the build log file.
    :return A 2-tuple: the status code, the errors data structure.
    """
    status = 200
    errors = {}

    database = utils.db.get_db_connection(db_options)
    json_obj = utils.db.find_one2(
        database[models.DEFCONFIG_COLLECTION], {models.ID_KEY: build_id})

    if json_obj:
        defconfig_doc = mdefconfig.DefconfigDocument.from_json(json_obj)
        if defconfig_doc:
            job = defconfig_doc.job
            kernel = defconfig_doc.kernel
            arch = defconfig_doc.arch
            defconfig_full = defconfig_doc.defconfig_full

            if defconfig_doc.dirname:
                build_dir = defconfig_doc.dirname
            else:
                build_dir = os.path.join(
                    base_path, job, kernel,
                    "%s-%s" % (arch, defconfig_full))

            log_file = os.path.join(build_dir, build_log)
            status, err_lines, warn_lines, mism_lines = _parse_log(
                job,
                kernel, defconfig_doc.defconfig, log_file, build_dir, errors)

            if status == 200:
                status = _save(
                    defconfig_doc,
                    job_id,
                    err_lines, warn_lines, mism_lines, errors, db_options)
    else:
        status = 500
        utils.LOG.warn("No build ID found, cannot continue parsing logs")
        ERR_ADD(errors, status, "No build ID found, cannot parse logs")

    return status, errors
