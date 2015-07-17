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

import models
import utils.log

BASE_PATH = "/var/www/images/kernel-ci"
DEFAULT_MONGODB_URL = "localhost"
DEFAULT_MONGODB_PORT = 27017
DEFAULT_MONGODB_POOL = 250
LOG = utils.log.get_log()

# Pattern used for glob matching files on the filesystem.
BOOT_REPORT_PATTERN = "boot-*.json"

# Build log file names.
BUILD_LOG_FILE = "build.log"
BUILD_ERRORS_FILE = "build-errors.log"
BUILD_WARNINGS_FILE = "build-warnings.log"
BUILD_MISMATCHES_FILE = "build-mismatches.log"


def valid_name(name):
    """Check if a job or kernel name is valid.

    A valid name must not:
    - start with a dot .
    - contain a dollar $
    - contain /

    :return True or False
    """
    is_valid = True
    if any([name.startswith("."), "$" in name, "/" in name]):
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


def get_defconfig_full(build_dir,
                       defconfig, defconfig_full, kconfig_fragments):
    """Get the value for defconfig_full variable based on available ones.

    :param build_dir: The directory we are parsing.
    :type build_dir: string
    :param defconfig: The value for defconfig
    :type defconfig: string
    :param defconfig_full: The possible value for defconfig_full as taken from
    the build json file.
    :type defconfig_full: string
    :param kconfig_fragments: The config fragments value where to start.
    :type kconfig_fragments: string
    :return The defconfig_full value.
    """
    if all([defconfig_full is None, kconfig_fragments is None]):
        defconfig_full = defconfig
    elif all([defconfig_full is None, kconfig_fragments is not None]):
        # Infer the real defconfig used from the values we have.
        # Try first from the kconfig_fragments and then from the
        # directory we are traversing.
        defconfig_full_k = \
            _extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        defconfig_full_d = \
            _extrapolate_defconfig_full_from_dirname(build_dir)

        # Default to use the one from kconfig_fragments.
        defconfig_full = defconfig_full_k
        # Use the one from the directory only if it is different from
        # the one obtained via the kconfig_fragments and if it is
        # different from the default defconfig value.
        if all([
                defconfig_full_d is not None,
                defconfig_full_d != defconfig_full_k,
                defconfig_full_d != defconfig]):
            defconfig_full = defconfig_full_k

    return defconfig_full


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
    if all([kconfig_fragments.startswith("frag-"),
            kconfig_fragments.endswith(".config")]):

        defconfig_full = "%s+%s" % (
            defconfig,
            kconfig_fragments.replace("frag-", "").replace(".config", ""))
    return defconfig_full


def _extrapolate_defconfig_full_from_dirname(dirname):
    """Try to extrapolate a valid defconfig_full value from the directory name.

    The directory we are traversing are built with the following pattern:

        ARCH-DEFCONFIG[+FRAGMENTS]

    We strip the ARCH part and keep only the rest.

    :param dirname: The name of the directory we are traversing.
    :type dirname: str
    :return None if the directory name does not match a valid pattern, or
    the value extrapolated from it.
    """
    def _replace_arch_value(arch, dirname):
        """Local function to replace the found arch value.

        :param arch: The name of the architecture.
        :type arch: str
        :param dirname: The name of the directory.
        :param dirname: str
        :return The directory name without the architecture value.
        """
        return dirname.replace("%s-" % arch, "", 1)

    defconfig_full = None
    for arch in models.VALID_ARCHITECTURES:
        if arch in dirname:
            defconfig_full = _replace_arch_value(arch, dirname)
            break

    return defconfig_full
