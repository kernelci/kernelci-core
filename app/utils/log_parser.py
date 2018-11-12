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

import bson
import datetime
import io
import itertools
import os
import re
import redis

import models
import models.build as mbuild
import models.error_log as merrl
import models.error_summary as mesumm
import utils
import utils.build
import utils.database.redisdb as redisdb
import utils.errors

ERROR_PATTERN_1 = re.compile("[Ee]rror:")
ERROR_PATTERN_2 = re.compile("^ERROR")
ERROR_PATTERN_3 = re.compile("undefined reference", re.IGNORECASE)
ERROR_PATTERN_4 = re.compile("gcc doesn't support", re.IGNORECASE)
ERROR_PATTERN_5 = re.compile("command not found", re.IGNORECASE)
ERROR_PATTERN_6 = re.compile("^\/bin\/([bd]a)?sh", re.IGNORECASE)
ERROR_PATTERN_7 = re.compile("^\/bin\/((tc)?z?c?k?)?sh", re.IGNORECASE)
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
    # Exclude also the mismatch pattern, and treat it separately.
    MISMATCH_PATTERN,
    NO_WARNING_PATTERN_1,
    NO_WARNING_PATTERN_2,
    NO_WARNING_PATTERN_3
]

ERROR_PATTERNS = [
    ERROR_PATTERN_1,
    ERROR_PATTERN_2,
    ERROR_PATTERN_3,
    ERROR_PATTERN_4,
    ERROR_PATTERN_5,
    ERROR_PATTERN_6,
    ERROR_PATTERN_7
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


# pylint: disable=too-many-branches
def _update_prev_summary(prev_doc, errors, warnings, mismatches, database):
    """Update a summary document with new log data.

    :param prev_doc: The previous error summary document.
    :type prev_doc: dict
    :param errors: The error lines and their count.
    :type errors: dict
    :param warnings: The warning lines and their count.
    :type warnings: dict
    :param mismatches: The mismatched lines and their count.
    :type mismatches: dict
    :param database: The database connection.
    :return The return value of the update operation.
    """

    def _update_summary_data(prev_data, new_data):
        """Create a new summary data structure based on the new and old values.

        :param prev_data: The data found in the document stored in the
        database.
        :type prev_data: dict
        :param new_data: The log data as processed.
        :type new_data: dict
        """
        # First create a new dict based on the old values.
        # The old value is a list of 2-tuples and we invert the values found in
        # there: k, v = tuple[1], tuple[0]
        prev_data_dict = dict((v, k) for k, v in prev_data)

        # Loop through the new data and look for old values to update.
        # This is done to update the sum of the log lines found.
        for key, val in new_data.iteritems():
            if key in prev_data_dict.viewkeys():
                prev_data_dict[key] += val
            else:
                prev_data_dict[key] = val

        return _dict_to_list(prev_data_dict)

    doc_get = prev_doc.get
    if errors:
        prev_errors = doc_get(models.ERRORS_KEY, None)
        if prev_errors:
            prev_doc[models.ERRORS_KEY] = _update_summary_data(
                prev_errors, errors)
        else:
            prev_doc[models.ERRORS_KEY] = _dict_to_list(errors)

    if mismatches:
        prev_mismatches = doc_get(models.MISMATCHES_KEY, None)
        if prev_mismatches:
            prev_doc[models.MISMATCHES_KEY] = _update_summary_data(
                prev_mismatches, mismatches)
        else:
            prev_doc[models.MISMATCHES_KEY] = _dict_to_list(mismatches)

    if warnings:
        prev_warnings = doc_get(models.WARNINGS_KEY, None)
        if prev_warnings:
            prev_doc[models.WARNINGS_KEY] = _update_summary_data(
                prev_warnings, warnings)
        else:
            prev_doc[models.WARNINGS_KEY] = _dict_to_list(warnings)

    ret_val = utils.db.find_and_update(
        database[models.ERRORS_SUMMARY_COLLECTION],
        {models.ID_KEY: prev_doc[models.ID_KEY]},
        {
            models.ERRORS_KEY: prev_doc[models.ERRORS_KEY],
            models.MISMATCHES_KEY: prev_doc[models.MISMATCHES_KEY],
            models.WARNINGS_KEY: prev_doc[models.WARNINGS_KEY]
        }
    )
    return ret_val


# pylint: disable=too-many-arguments
def _create_new_summary(
        errors, warnings, mismatches, job_id, build_doc, database):
    """Save a new error summary in the database.

    :param errors:
    :type errors: dict
    :param warnings:
    :type warnings: dict
    :param mismatches:
    :type mismatches:
    :param job_id:
    :type job_id: bson.objectid.ObjectId
    :param build_doc: The BuildDocument.
    :type build_doc: BuildDocument
    :param database: The database connection.
    :return The return value from the save operation.
    """
    error_summary = mesumm.ErrorSummaryDocument(job_id, "1.1")
    error_summary.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    error_summary.job = build_doc.job
    error_summary.kernel = build_doc.kernel
    error_summary.git_branch = build_doc.git_branch

    # Store the summary as lists of 2-tuple values.
    error_summary.errors = _dict_to_list(errors)
    error_summary.mismatches = _dict_to_list(mismatches)
    error_summary.warnings = _dict_to_list(warnings)

    ret_val, _ = utils.db.save(database, error_summary, manipulate=True)
    return ret_val


def _save_summary(
        errors, warnings, mismatches, job_id, build_doc, db_options):
    """Save the summary for errors/warnings/mismatches found."""
    ret_val = 200
    if (errors or warnings or mismatches):
        prev_doc = None
        database = utils.db.get_db_connection(db_options)
        redis_conn = redisdb.get_db_connection(db_options)
        prev_spec = {
            models.JOB_ID_KEY: job_id,
            models.JOB_KEY: build_doc.job,
            models.KERNEL_KEY: build_doc.kernel,
            models.GIT_BRANCH_KEY: build_doc.git_branch
        }

        # We might being importing documents and parsing build logs from
        # multiple processes.
        # In order to avoid having wrong data in the database, lock the
        # process here looking for the previous summary.
        lock_key = "log-parser-{:s}".format(str(job_id))
        with redis.lock.Lock(redis_conn, lock_key, timeout=5):
            prev_doc = utils.db.find_one2(
                database[models.ERRORS_SUMMARY_COLLECTION], prev_spec)

            if prev_doc:
                ret_val = _update_prev_summary(
                    prev_doc, errors, warnings, mismatches, database)
            else:
                ret_val = _create_new_summary(
                    errors,
                    warnings, mismatches, job_id, build_doc, database)

    return ret_val


# pylint: disable=too-many-locals
def save_defconfig_errors(
        build_doc,
        job_id, error_lines, warning_lines, mismatch_lines, db_options):
    """Save the build errors found.

    Save in the database the extracted lines from the build log.

    :param job_id: The ID of the job.
    :type job_id: str
    :param job: The name of the job.
    :type job: str
    :param kernel: The name of the kernel.
    :type kernel: str
    :param defconfig: The defconfig value.
    :type defconfig: str
    :param defconfig_full: The full defconfig value.
    :type defconfig_full: str
    :param arch: The architecture type.
    :type arch: str
    :param build_status: The status of the build.
    :type build_status: str
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
    build_id = None
    database = utils.db.get_db_connection(db_options)
    if not build_doc.id:
        spec = {
            models.ARCHITECTURE_KEY: build_doc.arch,
            models.DEFCONFIG_FULL_KEY: build_doc.defconfig_full,
            models.DEFCONFIG_KEY: build_doc.defconfig,
            models.GIT_BRANCH_KEY: build_doc.git_branch,
            models.JOB_KEY: build_doc.job,
            models.KERNEL_KEY: build_doc.kernel
        }

        if job_id:
            spec[models.JOB_ID_KEY] = job_id

        doc = utils.db.find_one2(
            database[models.BUILD_COLLECTION],
            spec, fields=[models.ID_KEY])

        if doc:
            build_id = doc[models.ID_KEY]
        else:
            utils.LOG.warn(
                "No build ID found for %s-%s-%s (%s)",
                build_doc.job,
                build_doc.kernel,
                build_doc.defconfig_full, build_doc.arch
            )
    else:
        build_id = build_doc.id

    if build_id:
        prev_spec = {
            models.BUILD_ID_KEY: build_id
        }
    else:
        prev_spec = {
            models.ARCHITECTURE_KEY: build_doc.arch,
            models.DEFCONFIG_FULL_KEY: build_doc.defconfig_full,
            models.DEFCONFIG_KEY: build_doc.defconfig,
            models.GIT_BRANCH_KEY: build_doc.git_branch,
            models.JOB_KEY: build_doc.job,
            models.KERNEL_KEY: build_doc.kernel,
            models.STATUS_KEY: build_doc.status
        }
    prev_doc = utils.db.find_one2(
        database[models.ERROR_LOGS_COLLECTION],
        prev_spec, fields=[models.ID_KEY])

    err_doc = merrl.ErrorLogDocument(job_id, "1.1")
    err_doc.arch = build_doc.arch
    err_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    err_doc.defconfig = build_doc.defconfig
    err_doc.defconfig_full = build_doc.defconfig_full
    err_doc.build_id = build_id
    err_doc.errors = error_lines
    err_doc.errors_count = len(error_lines)
    err_doc.git_branch = build_doc.git_branch
    err_doc.job = build_doc.job
    err_doc.kernel = build_doc.kernel
    err_doc.mismatch_lines = len(mismatch_lines)
    err_doc.mismatches = mismatch_lines
    err_doc.status = build_doc.status
    err_doc.warnings = warning_lines
    err_doc.warnings_count = len(warning_lines)
    err_doc.file_server_resource = build_doc.file_server_resource
    err_doc.file_server_url = build_doc.file_server_url
    err_doc.compiler = build_doc.compiler
    err_doc.compiler_version = build_doc.compiler_version
    err_doc.compiler_version_ext = build_doc.compiler_version_ext
    err_doc.compiler_version_full = build_doc.compiler_version_full

    manipulate = True
    if prev_doc:
        manipulate = False
        err_doc.id = prev_doc[models.ID_KEY]

    ret_val, _ = utils.db.save(database, err_doc, manipulate=manipulate)

    return ret_val


def _update_build_doc(
        build_doc, job_id, errors, warnings, mismatches, db_options):
    """Update the build document with errors/warnings count.

    :param build_doc: The build doc as read from the system.
    :type build_doc: dict
    :param job_id: The id of the job.
    :type job_id: str
    :param errors: The errors count.
    :type errors: int
    :param warnings: The warnings count.
    :type warnings: int
    :param mismatches: The mismatches count.
    :type mismatches: int
    :param db_options: The database connection options.
    :type db_options: dict
    :return The update status result (200 or 500).
    """
    document = {
        models.ERRORS_KEY: errors,
        models.WARNINGS_KEY: warnings,
        models.MISMATCHES_KEY: mismatches
    }
    query = {
        models.ARCHITECTURE_KEY: build_doc.arch,
        models.DEFCONFIG_FULL_KEY: build_doc.defconfig_full,
        models.DEFCONFIG_KEY: build_doc.defconfig,
        models.GIT_BRANCH_KEY: build_doc.git_branch,
        models.JOB_KEY: build_doc.job,
        models.KERNEL_KEY: build_doc.kernel
    }

    if job_id:
        query[models.JOB_ID_KEY] = job_id

    database = utils.db.get_db_connection(db_options)
    return utils.db.find_and_update(
        database[models.BUILD_COLLECTION], query, document)


def _save(
        build_doc,
        job_id, err_lines, warn_lines, mism_lines, errors, db_options):
    """Save the found errors/warnings/mismatched lines in the db.

    Save for each build the found values and update the summary data
    structures that will contain all the found errors/warnings/mismatches.
    """
    status = save_defconfig_errors(
        build_doc, job_id, err_lines, warn_lines, mism_lines, db_options)

    if status == 500:
        err_msg = \
            "Error saving errors log document for {}-{}-{}-{}-{}".format(
                build_doc.job,
                build_doc.git_branch,
                build_doc.kernel, build_doc.arch, build_doc.defconfig_full)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, status, err_msg)

    all_errors, all_warnings, all_mismatches = count_lines(
        err_lines, warn_lines, mism_lines)

    # Update the build doc with the errors count.
    status = _update_build_doc(
        build_doc,
        job_id, len(err_lines), len(warn_lines), len(mism_lines), db_options)

    if status != 200:
        error_msg = \
            "Error updating build errors count for {}-{}-{}-{}-{}".format(
                build_doc.job,
                build_doc.git_branch,
                build_doc.kernel, build_doc.arch, build_doc.defconfig_full)
        utils.LOG.error(error_msg)
        ERR_ADD(errors, status, err_msg)

    # Once done, save the summary.
    status = _save_summary(
        all_errors,
        all_warnings, all_mismatches, job_id, build_doc, db_options)

    if status == 500:
        error_msg = "Error saving errors summary for {}-{}-{}-{}-{}".format(
            build_doc.job,
            build_doc.git_branch,
            build_doc.kernel, build_doc.arch, build_doc.defconfig_full)
        ERR_ADD(errors, status, error_msg)

    return status


# pylint: disable=too-many-statements
# def _parse_log(job, kernel, defconfig, log_file, build_dir, errors):
def _parse_log(build_doc, log_file, build_dir, errors):
    """Read the build log and extract the correct strs.

    Parse the build log extracting the errors/warnings/mismatches strs
    saving new files for each of the extracted value.

    :param build_doc: A BuildDocument.
    :param log_file: The file to parse.
    :param build_dir: The directory where the file is located.
    :return A status code (200 = OK, 500 = error) and
    the lines for errors, warnings and mismatches as lists.
    """
    def _save_lines(lines, filename):
        # TODO: count the lines here.
        if not lines:
            return
        with io.open(filename, mode="w") as w_file:
            for line in lines:
                w_file.write(line)
                w_file.write(u"\n")

    def _clean_path(line):
        """Strip the beginning of the line if it contains a special sequence.

        :param line: The line to clean.
        :type line: str
        :return The line without the special sequence.
        """
        if line.startswith("../"):
            line = line[3:]
        return line

    error_lines = []
    warning_lines = []
    mismatch_lines = []

    if not os.path.isfile(log_file):
        utils.LOG.warn("Build dir '%s' does not have a build log", build_dir)
        return 500, [], [], []

    errors_file = os.path.join(build_dir, utils.BUILD_ERRORS_FILE)
    warnings_file = os.path.join(build_dir, utils.BUILD_WARNINGS_FILE)
    mismatches_file = os.path.join(build_dir, utils.BUILD_MISMATCHES_FILE)

    utils.LOG.info("Parsing build log file '%s'", log_file)

    err_append = error_lines.append
    warn_append = warning_lines.append
    mismatch_append = mismatch_lines.append

    try:
        with io.open(log_file) as read_file:
            for line in read_file:
                if any(re.search(err_pattrn, line)
                       for err_pattrn in ERROR_PATTERNS):
                    line = line.strip()
                    err_append(_clean_path(line))
                    continue

                if re.search(WARNING_PATTERN, line) \
                        and not any(re.search(warn_pattrn, line)
                                    for warn_pattrn in EXCLUDE_PATTERNS):
                    line = line.strip()
                    warn_append(_clean_path(line))
                    continue

                if re.search(MISMATCH_PATTERN, line):
                    line = line.strip()
                    mismatch_append(_clean_path(line))
    except IOError, ex:
        err_msg = "Cannot read build log file {}".format(log_file)
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        status = 500
        ERR_ADD(errors, status, err_msg)
        return status, [], [], []

    try:
        _save_lines(error_lines, errors_file)
        _save_lines(warning_lines, warnings_file)
        _save_lines(mismatch_lines, mismatches_file)
    except IOError, ex:
        err_msg = "Error writing errors/warnings file for {}-{}-{}-{}".format(
            build_doc.job,
            build_doc.branch, build_doc.kernel, build_doc.defconfig_full
        )
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        status = 500
        ERR_ADD(errors, status, err_msg)
    else:
        status = 200
    return status, error_lines, warning_lines, mismatch_lines


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
        database[models.BUILD_COLLECTION], {models.ID_KEY: build_id})

    if json_obj:
        build_doc = mbuild.BuildDocument.from_json(json_obj)
        if build_doc:
            build_dir = os.path.join(
                base_path,
                build_doc.job,
                build_doc.git_branch,
                build_doc.kernel,
                build_doc.arch,
                build_doc.defconfig_full,
                build_doc.build_environment)

            log_file = os.path.join(build_dir, build_log)
            status, err_lines, warn_lines, mism_lines = _parse_log(
                build_doc, log_file, build_dir, errors)

            if status == 200:
                status = _save(
                    build_doc,
                    job_id,
                    err_lines, warn_lines, mism_lines, errors, db_options)
    else:
        status = 500
        utils.LOG.warn("No build ID found, cannot continue parsing logs")
        ERR_ADD(errors, status, "No build ID found, cannot parse logs")

    return status, errors
