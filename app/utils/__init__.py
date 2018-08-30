# Copyright (C) 2014 Linaro Ltd.
#
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

"""Common functions, variables for all kernelci utils modules."""

import bson
import os
import re

import models
import utils.log

BASE_PATH = "/var/www/images/kernel-ci"
LOG = utils.log.get_log()

# Pattern used for glob matching files on the filesystem.
BOOT_REPORT_PATTERN = "boot-*.json"

# Build log file names.
BUILD_LOG_FILE = "build.log"
BUILD_ERRORS_FILE = "build-errors.log"
BUILD_WARNINGS_FILE = "build-warnings.log"
BUILD_MISMATCHES_FILE = "build-mismatches.log"

# All the mongodb ID keys we use.
ID_KEYS = [
    models.BOOT_ID_KEY,
    models.BUILD_ID_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.LAB_ID_KEY,
    models.TEST_CASE_ID_KEY,
    models.TEST_GROUP_ID_KEY
]

NO_START_CHARS = re.compile(r"^[^a-zA-Z0-9]")
NO_END_CHARS = re.compile(r"[^a-zA-Z0-9]$")
VALID_TEST_NAME = re.compile(r"[^a-zA-Z0-9\.\-_+]")
VALID_KCI_NAME = re.compile(r"[^a-zA-Z0-9\.\-_+=]")


def clean_branch_name(branch):
    """Clean up the branch name we get from a build.

    Previously, branch names could be like:

        local/for-next
        local/linux-4.4.y

    We are not interested in the "local/" part so we clean it out.

    :param branch: The name of the branch.
    :type branch: str
    :return The cleaned branch name or the same one.
    :rtpye str
    """
    valid_branch = branch
    if branch:
        parts = branch.split("/")
        valid_branch = parts[-1]
    return valid_branch


def update_id_fields(spec):
    """Make sure ID fields are treated correctly.

    Update in-place ID fields to perform a search.

    If we search for an ID field, either _id or like job_id, that references
    a real _id in mongodb, we need to make sure they are treated as such.
    mongodb stores them as ObjectId elements.

    :param spec: The spec data structure with the parameters to check.
    :type spec: dict
    """
    if spec:
        common_keys = list(set(ID_KEYS) & set(spec.viewkeys()))
        for key in common_keys:
            try:
                spec[key] = bson.objectid.ObjectId(spec[key])
            except bson.errors.InvalidId, ex:
                # We remove the key since it won't serve anything good.
                utils.LOG.error(
                    "Wrong ID value for key '%s', got '%s': ignoring",
                    key, spec[key])
                utils.LOG.exception(ex)
                spec.pop(key, None)


def valid_name(name):
    """Check if a job or kernel name is valid.

    A valid name must start and end with an alphanumeric character, and must
    match the following regex:

    [a-zA-Z0-9.-_+=]+

    :param name: The name to test.
    :type name: str
    :return True or False.
    :rtype bool
    """
    is_valid = True
    if any([NO_START_CHARS.match(name),
            NO_END_CHARS.search(name), VALID_KCI_NAME.search(name)]):
        is_valid = False
    return is_valid


def valid_test_name(name):
    """Check if a test name is valid or not.

    A valid name must start and end with an alphanumeric character, and must
    match the following regex:

    [a-zA-Z0-9.-_+]+

    :param name: The name to test.
    :type name: str
    :return True or False.
    :rtype bool
    """
    is_valid = True
    if any([NO_START_CHARS.match(name),
            NO_END_CHARS.search(name), VALID_TEST_NAME.search(name)]):
        is_valid = False
    return is_valid


def is_hidden(value):
    """Verify if a file name or dir name is hidden (starts with .).

    :param value: The value to verify.
    :return True or False.
    """
    hidden = False
    if value.startswith("."):
        hidden = True
    return hidden


def is_lab_dir(value):
    """Verify if a file name or dir name is a lab one.

    A lab dir name starts with lab-.

    :param value: The value to verify.
    :return True or False.
    """
    is_lab = False
    if value.startswith("lab-"):
        is_lab = True
    return is_lab


# pylint: disable=invalid-name
def _extrapolate_defconfig_full_from_kconfig(kconfig_fragments, defconfig):
    """Try to extrapolate a valid value for the defconfig_full argument.

    When the kconfig_fragments filed is defined, it should have a default
    structure.

    :param kconfig_fragments: The config fragments value where to start.
    :type kconfig_fragments: str
    :param defconfig: The defconfig value to use. Will be returned if
    `kconfig_fragments` does not match the known ones.
    :type defconfig: str
    :return A string with the `defconfig_full` value or the provided
    `defconfig`.
    """
    defconfig_full = defconfig
    if (kconfig_fragments.startswith("frag-") and
            kconfig_fragments.endswith(".config")):

        defconfig_full = "%s+%s" % (
            defconfig,
            kconfig_fragments.replace("frag-", "").replace(".config", ""))
    return defconfig_full


def get_defconfig_full(
        build_dir, defconfig, defconfig_full, kconfig_fragments):
    """Get the value for defconfig_full variable based on available ones.

    :param build_dir: The directory we are parsing.
    :type build_dir: string
    :param defconfig: The value for defconfig.
    :type defconfig: string
    :param defconfig_full: The possible value for defconfig_full as taken from
    the build json file.
    :type defconfig_full: string
    :param kconfig_fragments: The config fragments value where to start.
    :type kconfig_fragments: string
    :return The defconfig_full value.
    """
    if (defconfig_full is None and kconfig_fragments is None):
        defconfig_full = defconfig
    elif (defconfig_full is None and kconfig_fragments is not None):
        # Infer the real defconfig used from the values we have.
        # Try first from the kconfig_fragments and then from the
        # directory we are traversing.
        defconfig_full_k = \
            _extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        defconfig_full_d = os.path.basename(build_dir)

        # Default to use the one from kconfig_fragments.
        defconfig_full = defconfig_full_k
        # Use the one from the directory only if it is different from
        # the one obtained via the kconfig_fragments and if it is
        # different from the default defconfig value.
        if (defconfig_full_d is not None and
                defconfig_full_d != defconfig_full_k and
                defconfig_full_d != defconfig):
            defconfig_full = defconfig_full_k

    return defconfig_full
