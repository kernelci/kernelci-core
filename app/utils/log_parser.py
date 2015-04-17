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

import bson
import datetime
import io
import itertools
import os
import re
import types

import models
import models.error_log as merrl
import models.error_summary as mesumm
import utils


ERROR_PATTERN_1 = re.compile("[Ee]rror:")
ERROR_PATTERN_2 = re.compile("^ERROR")
WARNING_PATTERN = re.compile("warning:?", re.IGNORECASE)
MISMATCH_PATTERN = re.compile("Section mismatch", re.IGNORECASE)

# Regex pattern to exclude.
NO_WARNING_PATTERN_1 = re.compile(
    # pylint: disable=fixme
    "TODO: return_address should use unwind tables", re.IGNORECASE)
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
        errors[500] = ["No job ID specified, cannot continue"]

    return status, errors


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
def _traverse_dir_and_parse(job_id,
                            job,
                            kernel, base_path, build_log, db_options=None):
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

    res_keys = errors.viewkeys()
    hidden = utils.is_hidden

    errors_all = {}
    warnings_all = {}
    mismatches_all = {}

    err_default = errors_all.setdefault
    warn_default = warnings_all.setdefault
    mism_default = mismatches_all.setdefault

    def _dict_to_list(data):
        """Transform a dictionary into a list of tuples.

        :param data: The dictionary to transform.
        :return A list of tuples.
        """
        tupl = zip(data.values(), data.keys())
        tupl.sort()
        tupl.reverse()
        return tupl

    def _add_err_msg(err_code, err_msg):
        """Add error code and message to the data structure.

        :param err_code: The error code.
        :type err_code: integer
        :param err_msg: The error message.
        :"type err_msg: string, list
        """
        if err_code not in res_keys:
            errors[err_code] = []
        else:
            if isinstance(err_msg, types.ListType):
                errors[err_code].extend(err_msg)
            else:
                errors[err_code].append(err_msg)

    def _save(defconfig,
              defconfig_full,
              arch, build_status, error_lines, warning_lines, mismatch_lines):
        """Save the found errors/warnings/mismatched lines in the db.

        Save for each defconfig the found values and update the summary data
        structures that will contain all the found errors/warnings/mismatches.

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
        """
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

            status = save_defconfig_errors(
                job_id,
                job,
                kernel,
                defconfig,
                defconfig_full,
                arch,
                build_status,
                error_lines, warning_lines, mismatch_lines, db_options
            )

            if status == 500:
                error = "Error saving errors log document for %s-%s-%s (%s)"
                utils.LOG.error(error, job, kernel, defconfig_full, arch)
                _add_err_msg(
                    status, error % (job, kernel, defconfig_full, arch))

    def _save_summary():
        """Save the summary for errors/warnings/mismatches found."""
        # Save it only if we have something to save.
        if any([errors_all, warnings_all, mismatches_all]):
            error_summary = mesumm.ErrorSummaryDocument(job_id, "1.0")
            error_summary.created_on = datetime.datetime.now(
                tz=bson.tz_util.utc)
            error_summary.job = job
            error_summary.kernel = kernel

            # Store the summary as lists of 2-tuple values.
            error_summary.errors = _dict_to_list(errors_all)
            error_summary.mismatches = _dict_to_list(mismatches_all)
            error_summary.warnings = _dict_to_list(warnings_all)

            database = utils.db.get_db_connection(db_options)
            ret_val, _ = utils.db.save(
                database, error_summary, manipulate=True)

            if ret_val == 500:
                error = "Error saving errors summary for %s-%s (%s)"
                utils.LOG.error(error, job, kernel, job_id)
                _add_err_msg(ret_val, error % (job, kernel, job_id))

    def _read_build_data(build_dir):
        """Locally read the build JSON file to retrieve some values.

        Search for the correct defconfig, defconfig_full and arch values.

        :param build_dir: The directory containing the build JSON file.
        :type build_dir: string
        :return A 4-tuple: defconfig, defconfig_full, arch and build status.
        """
        arch = defconfig = defconfig_full = kconfig_fragments = b_status = None
        build_file = os.path.join(build_dir, models.BUILD_META_JSON_FILE)

        if os.path.isfile(build_file):
            build_data = None
            with io.open(build_file, "r") as read_file:
                build_data = json.load(read_file)

            if all([build_data, isinstance(build_data, types.DictionaryType)]):
                # pylint: disable=maybe-no-member
                b_get = build_data.get
                defconfig = b_get(models.DEFCONFIG_KEY)
                arch = b_get(
                    models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)
                defconfig_full = b_get(models.DEFCONFIG_FULL_KEY, None)
                kconfig_fragments = b_get(models.KCONFIG_FRAGMENTS_KEY, None)
                b_status = b_get(models.BUILD_RESULT_KEY, None)

                defconfig_full = utils.get_defconfig_full(
                    build_dir, defconfig, defconfig_full, kconfig_fragments)
            else:
                error = (
                    "No valid JSON data found in the build file for "
                    "%s - %s (%s)")
                utils.LOG.warn(error, job, kernel, build_dir)
                _add_err_msg(500, (error % (job, kernel, build_dir)))
        else:
            error = "Missing build file for %s - %s (%s)"
            utils.LOG.warn(error, job, kernel, build_dir)
            _add_err_msg(500, (error % (job, kernel, build_dir)))

        return defconfig, defconfig_full, arch, b_status

    if any([hidden(job), hidden(kernel)]):
        utils.LOG.error(
            "Wrong value passed for job and/or kernel: %s - %s", job, kernel)
        status = 500
        _add_err_msg(500, "Cannot work with hidden directories")
    else:
        job_dir = os.path.join(base_path, job)
        kernel_dir = os.path.join(job_dir, kernel)

        if os.path.isdir(kernel_dir):
            for dirname, subdirs, files in os.walk(kernel_dir):
                if dirname == kernel_dir:
                    continue

                subdirs[:] = []
                build_dir = dirname
                defconfig_dir = os.path.basename(build_dir)

                if not hidden(defconfig_dir):
                    log_file = os.path.join(build_dir, build_log)

                    defconfig, defconfig_full, arch, b_status = \
                        _read_build_data(build_dir)

                    status, err, e_l, w_l, m_l = _parse_log(
                        job, kernel, defconfig, log_file, build_dir)

                    if status == 200:
                        _save(
                            defconfig,
                            defconfig_full, arch, b_status, e_l, w_l, m_l
                        )
                    else:
                        _add_err_msg(status, err)

            # Once done, save the summary.
            _save_summary()
        else:
            error = "Provided values (%s,%s) do not match a directory"
            utils.LOG.error(error, job, kernel)
            status = 500
            _add_err_msg(500, error % (job, kernel))

    return status, errors


# pylint: disable=too-many-statements
def _parse_log(job, kernel, defconfig, log_file, build_dir):
    """Read the build log and extract the correct strings.

    Parse the build log extracting the errors/warnings/mismatches strings
    saving new files for each of the extracted value.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param defconfig: The name of the defconfig.
    :param log_file: The file to parse.
    :param build_dir: The directory where the file is located.
    :return A status code (200 = OK, 500 = error), a list of errors and
    the lines for errors, warnings and mismatches as lists.
    """
    utils.LOG.info("Parsing build log file '%s'", log_file)

    errors = []
    status = 200

    error_lines = []
    warning_lines = []
    mismatch_lines = []

    errors_file = os.path.join(build_dir, utils.BUILD_ERRORS_FILE)
    warnings_file = os.path.join(build_dir, utils.BUILD_WARNINGS_FILE)
    mismatches_file = os.path.join(build_dir, utils.BUILD_MISMATCHES_FILE)

    if os.path.isfile(log_file):
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
                            err_append(line)
                            break

                    if not has_err:
                        if re.search(WARNING_PATTERN, line):
                            for warn_pattrn in EXCLUDE_PATTERNS:
                                if re.search(warn_pattrn, line):
                                    break
                            else:
                                has_warn = True
                                line = line.strip()
                                warn_append(line)

                    if any([not has_err, not has_warn]):
                        if re.search(MISMATCH_PATTERN, line):
                            line = line.strip()
                            mismatch_append(line)
        except IOError, ex:
            error = "Cannot open build log file for %s-%s-%s"
            utils.LOG.exception(ex)
            utils.LOG.error(error, job, kernel, defconfig)
            status = 500
            errors.append(error % (job, kernel, defconfig))
        else:
            # Save only if we parsed something.
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
                error = "Error writing to errors/warnings file for %s-%s-%s"
                utils.LOG.exception(ex)
                utils.LOG.error(error, job, kernel, defconfig)
                status = 500
                errors.append(error % (job, kernel, defconfig))
    else:
        status = 500
        errors.append("Build dir %s does not have a build log" % defconfig)

    return status, errors, error_lines, warning_lines, mismatch_lines


def save_defconfig_errors(job_id,
                          job,
                          kernel,
                          defconfig,
                          defconfig_full,
                          arch,
                          build_status,
                          error_lines,
                          warning_lines, mismatch_lines, db_options):
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

    spec = {
        models.JOB_ID_KEY: job_id,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.ARCHITECTURE_KEY: arch
    }

    if defconfig:
        spec[models.DEFCONFIG_KEY] = defconfig
    if defconfig_full:
        spec[models.DEFCONFIG_FULL_KEY] = defconfig_full

    database = utils.db.get_db_connection(db_options)
    defconf_doc = utils.db.find_one2(
        database[models.DEFCONFIG_COLLECTION], spec, fields=[models.ID_KEY])

    if defconf_doc:
        defconfig_id = defconf_doc[models.ID_KEY]
    else:
        error = "No defconfig ID found for %s-%s-%s (%s)"
        utils.LOG.warn(error, job, kernel, defconfig_full, arch)

    err_doc = merrl.ErrorLogDocument(job_id, "1.0")
    err_doc.arch = arch
    err_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
    err_doc.defconfig = defconfig
    err_doc.defconfig_full = defconfig_full
    err_doc.defconfig_id = defconfig_id
    err_doc.errors = error_lines
    err_doc.errors_count = len(error_lines)
    err_doc.job = job
    err_doc.kernel = kernel
    err_doc.mismatch_lines = len(mismatch_lines)
    err_doc.mismatches = mismatch_lines
    err_doc.status = build_status
    err_doc.warnings = warning_lines
    err_doc.warnings_count = len(warning_lines)

    ret_val, _ = utils.db.save(database, err_doc, manipulate=True)

    return ret_val
