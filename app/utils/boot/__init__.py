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

"""Container for all the boot import related functions."""

try:
    import simplejson as json
except ImportError:
    import json

import bson
import copy
import datetime
import errno
import io
import os
import pymongo
import re

import models
import models.boot as mboot
import utils
import utils.db
import utils.errors

try:  # Py3K compat
    basestring
except NameError:
    basestring = str

# Some dtb appears to be in a temp directory like 'tmp', and will results in
# some weird names.
TMP_RE = re.compile(r"tmp")

# Keys that need to be checked for None or null value.
NON_NULL_KEYS = [
    models.BOARD_KEY,
    models.DEFCONFIG_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY
]

# Local error function.
ERR_ADD = utils.errors.add_error


class BootImportError(Exception):
    """General boot import exceptions class."""


class BootValidationError(ValueError, BootImportError):
    """General error for values of boot data."""


def save_or_update(boot_doc, database, errors):
    """Save or update the document in the database.

    Check if we have a document available in the db, and in case perform an
    update on it.

    :param boot_doc: The boot document to save.
    :type boot_doc: BaseDocument
    :param database: The database connection.
    :param errors: Where errors should be stored.
    :type errors: dict
    :return The save action return code and the doc ID.
    """
    spec = {
        models.ARCHITECTURE_KEY: boot_doc.arch,
        models.BOARD_KEY: boot_doc.board,
        models.DEFCONFIG_FULL_KEY: (
            boot_doc.defconfig_full or boot_doc.defconfig),
        models.DEFCONFIG_KEY: boot_doc.defconfig,
        models.JOB_KEY: boot_doc.job,
        models.KERNEL_KEY: boot_doc.kernel,
        models.LAB_NAME_KEY: boot_doc.lab_name,
        models.GIT_BRANCH_KEY: boot_doc.git_branch
    }

    fields = [
        models.CREATED_KEY,
        models.ID_KEY,
    ]

    prev_doc = utils.db.find_one2(
        database[models.BOOT_COLLECTION], spec, fields=fields)

    if prev_doc:
        doc_get = prev_doc.get
        doc_id = doc_get(models.ID_KEY)
        boot_doc.id = doc_id
        boot_doc.created_on = doc_get(models.CREATED_KEY)

        utils.LOG.info("Updating boot document with id '%s'", doc_id)
        ret_val, _ = utils.db.save(database, boot_doc)
    else:
        ret_val, doc_id = utils.db.save(database, boot_doc, manipulate=True)

    if ret_val == 500:
        err_msg = (
            "Error saving/updating boot report in the database "
            "for '%s-%s-%s-%s (%s, %s)'" %
            (
                boot_doc.job,
                boot_doc.git_branch,
                boot_doc.kernel,
                boot_doc.defconfig_full, boot_doc.arch, boot_doc.board
            )
        )
        ERR_ADD(errors, ret_val, err_msg)

    return ret_val, doc_id


def save_to_disk(boot_doc, json_obj, base_path, errors):
    """Save the provided boot report to disk.

    :param boot_doc: The document parsed.
    :type boot_doc: models.boot.BootDocument
    :param json_obj: The JSON data to write.
    :type json_obj: dictionary
    :param base_path: The base path where to save the document.
    :type base_path: str
    :param errors: Where errors should be stored.
    :type errors: dictionary
    """
    dir_path = os.path.join(
        base_path,
        boot_doc.job,
        boot_doc.git_branch,
        boot_doc.kernel,
        boot_doc.arch,
        boot_doc.defconfig_full, boot_doc.lab_name)
    file_path = os.path.join(dir_path, "boot-{}.json".format(boot_doc.board))

    try:
        if not os.path.isdir(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError, ex:
                if ex.errno != errno.EEXIST:
                    raise ex

        with io.open(file_path, mode="w") as write_json:
            write_json.write(
                unicode(
                    json.dumps(
                        json_obj, indent="  ", default=bson.json_util.default),
                    encoding="utf-8"
                )
            )
    except (OSError, IOError), ex:
        err_msg = "Error saving boot report to '{}'".format(file_path)
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 500, err_msg)


def _get_boot_seconds(boot_dict):
    """Returns boot time in seconds"""
    try:
        boot_time_raw = boot_dict[models.BOOT_TIME_KEY]
    except KeyError:
        raise BootValidationError("Boot time missing")
    try:
        boot_time = float(boot_time_raw)
    except ValueError:
        raise BootValidationError(
            "Boot time is not a number: {!r}".format(boot_time_raw))
    if boot_time < 0.0:
        raise BootValidationError("Found negative boot time")
    return boot_time


def _seconds_as_datetime(seconds):
    """
    Returns seconds encoded as a point in time `seconds` seconds after since
    1970-01-01T00:00:00Z.
    """
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=seconds)


def _update_boot_doc_from_json(boot_doc, boot_dict, errors):
    """Update a BootDocument from the provided boot dictionary.

    This function does not return anything, and the BootDocument passed is
    updated from the values found in the provided JSON object.

    :param boot_doc: The BootDocument to update.
    :type boot_doc: `models.boot.BootDocument`.
    :param boot_dict: Boot dictionary.
    :type boot_dict: dict
    :param errors: Where errors should be stored.
    :type errors: dict
    """

    try:
        seconds = _get_boot_seconds(boot_dict)
    except BootValidationError as ex:
        seconds = 0.0
        err_msg = "Error reading boot time data; defaulting to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    try:
        boot_doc.time = _seconds_as_datetime(seconds)
    except OverflowError as ex:
        seconds = 0.0
        err_msg = "Boot time value is too large for a time value, default to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    if seconds == 0.0:
        boot_doc.time = _seconds_as_datetime(seconds)

    boot_doc.status = boot_dict.get(
        models.BOOT_RESULT_KEY, models.UNKNOWN_STATUS)
    boot_doc.board_instance = boot_dict.get(models.BOARD_INSTANCE_KEY, None)
    boot_doc.boot_log = boot_dict.get(models.BOOT_LOG_KEY, None)
    boot_doc.boot_log_html = boot_dict.get(models.BOOT_LOG_HTML_KEY, None)
    boot_doc.boot_result_description = boot_dict.get(
        models.BOOT_RESULT_DESC_KEY, None)
    boot_doc.device_type = boot_dict.get(models.DEVICE_TYPE_KEY, None)
    boot_doc.dtb = boot_dict.get(models.DTB_KEY, None)
    boot_doc.dtb_addr = boot_dict.get(models.DTB_ADDR_KEY, None)
    boot_doc.dtb_append = boot_dict.get(models.DTB_APPEND_KEY, None)
    boot_doc.endian = boot_dict.get(models.ENDIANNESS_KEY, None)
    boot_doc.fastboot = boot_dict.get(models.FASTBOOT_KEY, None)
    boot_doc.fastboot_cmd = boot_dict.get(models.FASTBOOT_CMD_KEY, None)
    boot_doc.file_server_resource = boot_dict.get(
        models.FILE_SERVER_RESOURCE_KEY, None)
    boot_doc.file_server_url = boot_dict.get(models.FILE_SERVER_URL_KEY, None)
    boot_doc.git_commit = boot_dict.get(models.GIT_COMMIT_KEY, None)
    boot_doc.git_describe = boot_dict.get(models.GIT_DESCRIBE_KEY, None)
    boot_doc.git_url = boot_dict.get(models.GIT_URL_KEY, None)
    boot_doc.initrd_addr = boot_dict.get(models.INITRD_ADDR_KEY, None)
    boot_doc.kernel_image = boot_dict.get(models.KERNEL_IMAGE_KEY, None)
    boot_doc.load_addr = boot_dict.get(models.BOOT_LOAD_ADDR_KEY, None)
    boot_doc.metadata = boot_dict.get(models.METADATA_KEY, {})
    boot_doc.qemu = boot_dict.get(models.QEMU_KEY, None)
    boot_doc.qemu_command = boot_dict.get(models.QEMU_COMMAND_KEY, None)
    boot_doc.retries = boot_dict.get(models.BOOT_RETRIES_KEY, 0)
    boot_doc.uimage = boot_dict.get(models.UIMAGE_KEY, None)
    boot_doc.uimage_addr = boot_dict.get(models.UIMAGE_ADDR_KEY, None)
    boot_doc.version = boot_dict.get(models.VERSION_KEY, "1.1")
    boot_doc.warnings = boot_dict.get(models.BOOT_WARNINGS_KEY, 0)
    boot_doc.bootloader = boot_dict.get(models.BOOTLOADER_TYPE_KEY, None)
    boot_doc.bootloader_version = boot_dict.get(
        models.BOOTLOADER_VERSION_KEY, None)
    boot_doc.chainloader = boot_dict.get(models.CHAINLOADER_TYPE_KEY, None)
    boot_doc.filesystem = boot_dict.get(models.FILESYSTEM_TYPE_KEY, None)
    boot_doc.boot_job_id = boot_dict.get(models.BOOT_JOB_ID_KEY, None)
    boot_doc.boot_job_path = boot_dict.get(models.BOOT_JOB_PATH_KEY, None)
    boot_doc.boot_job_url = boot_dict.get(models.BOOT_JOB_URL_KEY, None)

    # mach_alias_key takes precedence if defined
    boot_doc.mach = boot_dict.get(
        models.MACH_ALIAS_KEY, boot_dict.get(models.MACH_KEY, None))


def _check_for_null(board_dict):
    """Check if the board dictionary has values resembling None in its
    mandatory keys.

    Values must be different than:
    - None
    - ""
    - "null"

    :param board_dict: The board dictoinary.
    :type board_dict: dict

    :raise BootValidationError if any of the keys matches the condition.
    """
    for key in NON_NULL_KEYS:
        val = board_dict.get(key, None)
        if (val is None or
            (isinstance(val, basestring) and
                val.lower() in ('', 'null', 'none'))):
            raise BootValidationError(
                "Invalid value found for mandatory key {!r}: {!r}".format(
                    key, val))


def _update_boot_doc_ids(boot_doc, database):
    """Update boot document job and build IDs references.

    :param boot_doc: The boot document to update.
    :type boot_doc: BootDocument
    :param database: The database connection to use.
    """
    job = boot_doc.job
    kernel = boot_doc.kernel
    defconfig = boot_doc.defconfig
    defconfig_full = boot_doc.defconfig_full
    arch = boot_doc.arch
    branch = boot_doc.git_branch

    spec = {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.GIT_BRANCH_KEY: branch
    }

    job_doc = utils.db.find_one2(database[models.JOB_COLLECTION], spec)

    spec.update({
        models.ARCHITECTURE_KEY: arch,
        models.DEFCONFIG_KEY: defconfig,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel
    })

    if defconfig_full:
        spec[models.DEFCONFIG_FULL_KEY] = defconfig_full

    build_doc = utils.db.find_one2(database[models.BUILD_COLLECTION], spec)

    if job_doc:
        boot_doc.job_id = job_doc.get(models.ID_KEY, None)
    else:
        utils.LOG.warn(
            "No job document found for boot %s-%s-%s-%s (%s)",
            job, branch, kernel, defconfig_full, arch)

    if build_doc:
        doc_get = build_doc.get
        boot_doc.build_id = doc_get(models.ID_KEY, None)

        # In case we do not have the job_id key with the previous search.
        if all([not boot_doc.job_id, doc_get(models.JOB_ID_KEY, None)]):
            boot_doc.job_id = doc_get(models.JOB_ID_KEY, None)
        # Get also git information if we do not have them already,
        if not boot_doc.git_branch:
            boot_doc.git_branch = doc_get(models.GIT_BRANCH_KEY, None)
        if not boot_doc.git_commit:
            boot_doc.git_commit = doc_get(models.GIT_COMMIT_KEY, None)
        if not boot_doc.git_describe:
            boot_doc.git_describe = doc_get(models.GIT_DESCRIBE_KEY, None)
        if not boot_doc.git_url:
            boot_doc.git_url = doc_get(models.GIT_URL_KEY, None)
        if not boot_doc.compiler:
            boot_doc.compiler = doc_get(models.COMPILER_KEY, None)
        if not boot_doc.compiler_version_ext:
            boot_doc.compiler_version_ext = \
                doc_get(models.COMPILER_VERSION_EXT_KEY, None)
        if not boot_doc.compiler_version_full:
            boot_doc.compiler_version_full = \
                doc_get(models.COMPILER_VERSION_FULL_KEY, None)
        if not boot_doc.compiler_version:
            boot_doc.compiler_version = \
                doc_get(models.COMPILER_VERSION_KEY, None)
        if not boot_doc.cross_compile:
            boot_doc.cross_compile = doc_get(models.CROSS_COMPILE_KEY, None)

        # Pick the kernel image size as well.
        boot_doc.kernel_image_size = \
            doc_get(models.KERNEL_IMAGE_SIZE_KEY, None)
    else:
        utils.LOG.warn(
            "No build document found for boot %s-%s-%s-%s (%s)",
            job, branch, kernel, defconfig_full, arch)


def _parse_boot_from_json(boot_json, database, errors):
    """Parse the boot report from a JSON object.

    :param boot_json: The JSON object.
    :type boot_json: dict
    :param database: The database connection.
    :param errors: Where to store the errors.
    :type errors: dict
    :return A `models.boot.BootDocument` instance, or None if the JSON cannot
    be parsed correctly.
    """
    if not boot_json:
        return None

    try:
        _check_for_null(boot_json)
    except BootValidationError, ex:
        utils.LOG.exception(ex)
        ERR_ADD(errors, 400, str(ex))
        return None

    try:
        board = boot_json[models.BOARD_KEY]
        job = boot_json[models.JOB_KEY]
        kernel = boot_json[models.KERNEL_KEY]
        defconfig = boot_json[models.DEFCONFIG_KEY]
        lab_name = boot_json[models.LAB_NAME_KEY]
        git_branch = boot_json[models.GIT_BRANCH_KEY]
    except KeyError, ex:
        err_msg = "Missing mandatory key in boot data"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)
        return None

    defconfig_full = boot_json.get(models.DEFCONFIG_FULL_KEY, defconfig)
    arch = boot_json.get(models.ARCHITECTURE_KEY)
    boot_doc = mboot.BootDocument(
        board,
        job, kernel, defconfig, lab_name, git_branch, defconfig_full, arch)
    boot_doc.created_on = datetime.datetime.now(
        tz=bson.tz_util.utc)
    _update_boot_doc_from_json(boot_doc, boot_json, errors)
    _update_boot_doc_ids(boot_doc, database)
    return boot_doc


def import_and_save_boot(json_obj, db_options, base_path=utils.BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.
    Import and save the boot report as found from the parameters in the
    provided JSON object.

    :param json_obj: The JSON object with the values that identify the boot
    report log.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    ret_code = None
    doc_id = None
    errors = {}

    try:
        database = utils.db.get_db_connection(db_options)
        json_copy = copy.deepcopy(json_obj)

        doc = _parse_boot_from_json(json_copy, database, errors)
        if doc:
            ret_code, doc_id = save_or_update(doc, database, errors)
            save_to_disk(doc, json_obj, base_path, errors)
        else:
            utils.LOG.warn("No boot report imported nor saved")
    except pymongo.errors.ConnectionFailure, ex:
        utils.LOG.exception(ex)
        utils.LOG.error("Error getting database connection")
        ERR_ADD(errors, 500, "Error connecting to the database")
        raise utils.errors.BackendError(errors)

    return doc_id
