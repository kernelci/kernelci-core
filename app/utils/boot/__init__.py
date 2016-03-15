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
        models.LAB_NAME_KEY: boot_doc.lab_name
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
            "for '%s-%s-%s (%s, %s)'" %
            (
                boot_doc.job,
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
    job = boot_doc.job
    kernel = boot_doc.kernel
    defconfig_full = boot_doc.defconfig_full
    lab_name = boot_doc.lab_name
    board = boot_doc.board
    arch = boot_doc.arch

    r_defconfig = "-".join([arch, defconfig_full])

    dir_path = os.path.join(base_path, job, kernel, r_defconfig, lab_name)
    file_path = os.path.join(dir_path, "boot-%s.json" % board)

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
        err_msg = (
            "Error saving boot report to disk for '%s-%s-%s (%s, %s)'" %
            (
                boot_doc.job,
                boot_doc.kernel,
                boot_doc.defconfig_full, boot_doc.arch, boot_doc.board
            )
        )
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 500, err_msg)


def _update_boot_doc_from_json(boot_doc, json_pop_f, errors):
    """Update a BootDocument from the provided JSON boot object.

    This function does not return anything, and the BootDocument passed is
    updated from the values found in the provided JSON object.

    :param boot_doc: The BootDocument to update.
    :type boot_doc: `models.boot.BootDocument`.
    :param json_pop_f: The function used to pop elements out of the JSON
    object.
    :type json_pop_f: function
    :param errors: Where errors should be stored.
    :type errors: dict
    """
    boot_time = json_pop_f(models.BOOT_TIME_KEY, 0.0)
    try:
        seconds = float(boot_time)
    except ValueError, ex:
        # Default to 0.
        seconds = 0.0
        err_msg = (
            "Error reading boot time data, got: %s; defaulting to 0" %
            str(boot_time))
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    try:
        if seconds < 0.0:
            seconds = 0.0
            ERR_ADD(errors, 400, "Boot time is negative, defaulting to 0")

        if seconds == 0.0:
            boot_doc.time = datetime.datetime(
                1970, 1, 1, hour=0, minute=0, second=0)
        else:
            time_d = datetime.timedelta(seconds=seconds)
            boot_doc.time = datetime.datetime(
                1970, 1, 1,
                minute=time_d.seconds / 60,
                second=time_d.seconds % 60,
                microsecond=time_d.microseconds
            )
    except OverflowError, ex:
        # Default to 0 time.
        boot_doc.time = datetime.datetime(
            1970, 1, 1, hour=0, minute=0, second=0)
        err_msg = "Boot time value is too large for a time value, default to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    boot_doc.status = json_pop_f(
        models.BOOT_RESULT_KEY, models.UNKNOWN_STATUS)
    boot_doc.board_instance = json_pop_f(models.BOARD_INSTANCE_KEY, None)
    boot_doc.boot_log = json_pop_f(models.BOOT_LOG_KEY, None)
    boot_doc.boot_log_html = json_pop_f(models.BOOT_LOG_HTML_KEY, None)
    boot_doc.boot_result_description = json_pop_f(
        models.BOOT_RESULT_DESC_KEY, None)
    boot_doc.dtb = json_pop_f(models.DTB_KEY, None)
    boot_doc.dtb_addr = json_pop_f(models.DTB_ADDR_KEY, None)
    boot_doc.dtb_append = json_pop_f(models.DTB_APPEND_KEY, None)
    boot_doc.endian = json_pop_f(models.ENDIANNESS_KEY, None)
    boot_doc.fastboot = json_pop_f(models.FASTBOOT_KEY, None)
    boot_doc.fastboot_cmd = json_pop_f(models.FASTBOOT_CMD_KEY, None)
    boot_doc.file_server_resource = json_pop_f(
        models.FILE_SERVER_RESOURCE_KEY, None)
    boot_doc.file_server_url = json_pop_f(models.FILE_SERVER_URL_KEY, None)
    boot_doc.git_branch = json_pop_f(models.GIT_BRANCH_KEY, None)
    boot_doc.git_commit = json_pop_f(models.GIT_COMMIT_KEY, None)
    boot_doc.git_describe = json_pop_f(models.GIT_DESCRIBE_KEY, None)
    boot_doc.git_url = json_pop_f(models.GIT_URL_KEY, None)
    boot_doc.initrd_addr = json_pop_f(models.INITRD_ADDR_KEY, None)
    boot_doc.kernel_image = json_pop_f(models.KERNEL_IMAGE_KEY, None)
    boot_doc.load_addr = json_pop_f(models.BOOT_LOAD_ADDR_KEY, None)
    boot_doc.mach = json_pop_f(models.MACH_KEY, None)
    boot_doc.metadata = json_pop_f(models.METADATA_KEY, {})
    boot_doc.qemu = json_pop_f(models.QEMU_KEY, None)
    boot_doc.qemu_command = json_pop_f(models.QEMU_COMMAND_KEY, None)
    boot_doc.retries = json_pop_f(models.BOOT_RETRIES_KEY, 0)
    boot_doc.uimage = json_pop_f(models.UIMAGE_KEY, None)
    boot_doc.uimage_addr = json_pop_f(models.UIMAGE_ADDR_KEY, None)
    boot_doc.version = json_pop_f(models.VERSION_KEY, "1.0")
    boot_doc.warnings = json_pop_f(models.BOOT_WARNINGS_KEY, 0)
    boot_doc.bootloader = json_pop_f(models.BOOTLOADER_TYPE_KEY, None)
    boot_doc.bootloader_version = json_pop_f(
        models.BOOTLOADER_VERSION_KEY, None)
    boot_doc.chainloader = json_pop_f(models.CHAINLOADER_TYPE_KEY, None)
    boot_doc.filesystem = json_pop_f(models.FILESYSTEM_TYPE_KEY, None)


def _check_for_null(get_func):
    """Check if the json object has invalid values in its mandatory keys.

    An invalid value is either None or the "null" string.

    :param get_func: The get() function to retrieve the data.
    :type get_func: function

    :raise BootImportError in case of errors.
    """
    err_msg = "Invalid value found for mandatory key '%s': %s"

    for key in NON_NULL_KEYS:
        t_val = str(get_func(key, ""))

        val = t_val.lower()
        if any([not val, val == "null", val == "none"]):
            raise BootImportError(err_msg.format(key, t_val))


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

    job_doc = utils.db.find_one2(
        database[models.JOB_COLLECTION],
        {models.JOB_KEY: job, models.KERNEL_KEY: kernel}
    )

    build_spec = {
        models.ARCHITECTURE_KEY: arch,
        models.DEFCONFIG_KEY: defconfig,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel
    }

    if defconfig_full:
        build_spec[models.DEFCONFIG_FULL_KEY] = defconfig_full

    build_doc = utils.db.find_one2(
        database[models.BUILD_COLLECTION], build_spec)

    if job_doc:
        boot_doc.job_id = job_doc.get(models.ID_KEY, None)
    else:
        utils.LOG.warn(
            "No job document found for boot %s-%s-%s (%s)",
            job, kernel, defconfig_full, arch)

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
            "No build document found for boot %s-%s-%s (%s)",
            job, kernel, defconfig_full, arch)


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
    boot_doc = None

    if boot_json:
        try:
            json_pop_f = boot_json.pop
            json_get_f = boot_json.get

            _check_for_null(json_get_f)

            board = json_pop_f(models.BOARD_KEY)
            job = json_pop_f(models.JOB_KEY)
            kernel = json_pop_f(models.KERNEL_KEY)
            defconfig = json_pop_f(models.DEFCONFIG_KEY)
            defconfig_full = json_pop_f(models.DEFCONFIG_FULL_KEY, defconfig)
            lab_name = json_pop_f(models.LAB_NAME_KEY)
            arch = json_pop_f(
                models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)

            if not arch:
                arch = models.ARM_ARCHITECTURE_KEY

            if arch in models.VALID_ARCHITECTURES:
                boot_doc = mboot.BootDocument(
                    board,
                    job, kernel, defconfig, lab_name, defconfig_full, arch)
                boot_doc.created_on = datetime.datetime.now(
                    tz=bson.tz_util.utc)
                _update_boot_doc_from_json(boot_doc, json_pop_f, errors)
                _update_boot_doc_ids(boot_doc, database)
            else:
                raise BootImportError(
                    "Invalid architecture found: %s".format(arch))
        except KeyError, ex:
            err_msg = "Missing mandatory key in boot data"
            utils.LOG.exception(ex)
            utils.LOG.error(err_msg)
            ERR_ADD(errors, 400, err_msg)
        except BootImportError, ex:
            utils.LOG.exception(ex)
            ERR_ADD(errors, 400, str(ex))

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

    return ret_code, doc_id, errors
