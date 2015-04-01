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

import os
import re
import types

import models
import utils


ERROR_PATTERN = re.compile("^error:?", re.IGNORECASE)
WARNING_PATTERN = re.compile("warning:?", re.IGNORECASE)
MISMATCH_PATTERN = re.compile("Section mismatch", re.IGNORECASE)

# Regex pattern to exclude.
NO_WARNING_PATTERN_1 = re.compile(
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


def parse_build_log(json_obj,
                    base_path=utils.BASE_PATH, build_log=utils.BUILD_LOG_FILE):
    """Parse the build log file searching for errors and warnings.

    :param json_obj: The JSON object with the job and kernel name.
    :type json_obj: dictionary
    :param base_path: The path on the file system where the files are stored.
    :type base_path: string
    :param build_log: The name of the build log file.
    :type build_log: string
    :return A status code and a dictionary. 200 if everything is good, 500 in
    case of errors; an empty dictionary if there are no errors, otherwise the
    dictionary will contain error codes and messages lists.
    """
    j_get = json_obj.get
    job = j_get(models.JOB_KEY)
    kernel = j_get(models.KERNEL_KEY)

    return _traverse_dir_and_parse(job, kernel, base_path, build_log)


def _traverse_dir_and_parse(job, kernel, base_path, build_log):
    """
    """
    errors = {}
    status = 200

    res_keys = errors.viewkeys()

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

    if any([utils.is_hidden(job), utils.is_hidden(kernel)]):
        utils.LOG.error(
            "Wrong value passed for job and/or kernel: %s - %s", job, kernel)
        status = 500
        errors[500] = ["Cannot work with hidden directories"]
    else:
        job_dir = os.path.join(base_path, job)
        kernel_dir = os.path.join(job_dir, kernel)

        if os.path.isdir(kernel_dir):
            def _yield_parse_log():
                """
                """
                for defconfig in os.listdir(kernel_dir):
                    if not utils.is_hidden(defconfig):
                        build_dir = os.path.join(kernel_dir, defconfig)
                        log_file = os.path.join(build_dir, build_log)
                        yield _parse_build_log(
                            job, kernel, defconfig, log_file, build_dir)

            [
                _add_err_msg(status, err)
                for status, err in _yield_parse_log()
                if status != 200
            ]

            utils.LOG.info(errors)
        else:
            error = "Provided values (%s,%s) do not match a directory"
            utils.LOG.error(error, job, kernel)
            status = 500
            errors[500] = [
                "Provided values (%s,%s) do not match a directory" %
                (job, kernel)
            ]

    return status, errors


def _parse_build_log(job, kernel, defconfig, log_file, build_dir):
    """
    """
    utils.LOG.info("Parsing build log file '%s'", log_file)

    errors = []
    status = 200

    errors_file = os.path.join(build_dir, utils.BUILD_ERRORS_FILE)
    warnings_file = os.path.join(build_dir, utils.BUILD_WARNINGS_FILE)

    if os.path.isfile(log_file):
        try:
            with open(log_file) as read_file, \
                    open(errors_file, "w") as err_file, \
                    open(warnings_file, "w") as warn_file:
                for line in read_file:
                    # TODO
                    line = line.strip()
                    err_file.write(line)
                    warn_file.write(line)
        except IOError, ex:
            error = "Cannot open files for %s-%s-%s"
            utils.LOG.exception(ex)
            utils.LOG.error(error, job, kernel, defconfig)
            status = 500
            errors.append(error % (job, kernel, defconfig))
    else:
        status = 500
        errors.append("Build dir %s does not have a build log" % defconfig)

    return status, errors


if __name__ == "__main__":
    parse_build_log(
        {"job": "next", "kernel": "next-20150401"},
        base_path="/Users/milo/Development/var/build-logs"
    )
