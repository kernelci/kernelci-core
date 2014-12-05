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

"""Container for all the boot import related functions."""

try:
    import simplejson as json
except ImportError:
    import json

import bson
import copy
import datetime
import glob
import os
import re

import models
import models.boot as modbt
import utils
import utils.db

# Pattern used for glob matching files on the filesystem.
BOOT_REPORT_PATTERN = 'boot-*.json'

# Some dtb appears to be in a temp directory like 'tmp', and will results in
# some weird names.
TMP_RE = re.compile(r'tmp')


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
    database = utils.db.get_db_connection(db_options)
    json_copy = copy.deepcopy(json_obj)

    doc = _parse_boot_from_json(json_copy, database)
    doc_id = None
    ret_code = None

    if doc:
        ret_code, doc_id = save_or_update(doc, database)
        save_to_disk(doc, json_obj, base_path)
    else:
        utils.LOG.info("Boot report not imported nor saved")

    return ret_code, doc_id


def save_or_update(boot_doc, database):
    """Save or update the document in the database.

    Check if we have a document available in the db, and in case perform an
    update on it.

    :param boot_doc: The boot document to save.
    :type boot_doc: BaseDocument
    :param database: The database connection.
    :return The save action return code and the doc ID.
    """
    spec = {
        models.LAB_NAME_KEY: boot_doc.lab_name,
        models.NAME_KEY: boot_doc.name,
    }

    fields = [
        models.CREATED_KEY,
        models.ID_KEY,
    ]

    found_doc = utils.db.find(
        database[models.BOOT_COLLECTION], 1, 0, spec=spec, fields=fields)

    prev_doc = None
    doc_len = found_doc.count()
    if doc_len == 1:
        prev_doc = found_doc[0]

    if prev_doc:
        doc_get = prev_doc.get
        doc_id = doc_get(models.ID_KEY)
        boot_doc.id = doc_id
        boot_doc.created_on = doc_get(models.CREATED_KEY)

        utils.LOG.info("Updating boot document with id '%s'", doc_id)
        ret_val, _ = utils.db.save(database, boot_doc)
    else:
        ret_val, doc_id = utils.db.save(database, boot_doc, manipulate=True)

    return ret_val, doc_id


def save_to_disk(boot_doc, json_obj, base_path):
    """Save the provided boot report to disk.

    :param boot_doc: The document parsed.
    :type boot_doc: models.boot.BootDocument
    :param json_obj: The JSON object to save.
    :type json_obj: dict
    :param base_path: The base path where to save the document.
    :type base_path: str
    """
    job = boot_doc.job
    kernel = boot_doc.kernel
    defconfig = boot_doc.defconfig_full
    lab_name = boot_doc.lab_name
    board = boot_doc.board
    arch = boot_doc.arch

    r_defconfig = "-".join([arch, defconfig])

    dir_path = os.path.join(base_path, job, kernel, r_defconfig, lab_name)
    file_path = os.path.join(dir_path, 'boot-%s.json' % board)

    try:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        with open(file_path, mode="w") as write_json:
            write_json.write(
                json.dumps(json_obj, encoding="utf_8", ensure_ascii=False)
            )
    except (OSError, IOError), ex:
        utils.LOG.error(
            "Error saving document '%s' into '%s'",
            boot_doc.name, dir_path
        )
        utils.LOG.exception(ex)


def _parse_boot_from_file(boot_log):
    """Read and parse the actual boot report.

    :param boot_log: The path to the boot report.
    :return A `BootDocument` object.
    """

    utils.LOG.info("Parsing boot log file '%s'", boot_log)

    boot_json = None
    boot_doc = None

    try:
        with open(boot_log) as read_f:
            boot_json = json.load(read_f)

        json_pop_f = boot_json.pop

        # Mandatory fields.
        job = json_pop_f(models.JOB_KEY)
        kernel = json_pop_f(models.KERNEL_KEY)
        defconfig = json_pop_f(models.DEFCONFIG_KEY)
        defconfig_full = json_pop_f(models.DEFCONFIG_FULL_KEY, defconfig)
        lab_name = json_pop_f(models.LAB_NAME_KEY)
        arch = json_pop_f(models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)
        # Even if board is mandatory, for old cases this used not to be true.
        board = json_pop_f(models.BOARD_KEY, None)
        dtb = boot_json.get(models.DTB_KEY, None)

        if not board:
            utils.LOG.info("No board value specified in the boot report")
            if dtb and not TMP_RE.findall(dtb):
                board = os.path.splitext(os.path.basename(dtb))[0]
            else:
                # If we do not have the dtb field we use the boot report file to
                # extract some kind of value for board.
                board = os.path.splitext(
                    os.path.basename(boot_log).replace('boot-', ''))[0]
                utils.LOG.info(
                    "Using boot report file name for board name: %s", board
                )

        boot_doc = modbt.BootDocument(
            board, job, kernel, defconfig, lab_name, defconfig_full, arch)
        _update_boot_doc_from_json(boot_doc, boot_json, json_pop_f)
        # TODO: Find and add job_id and defconfig_id
    except (OSError, TypeError, IOError), ex:
        utils.LOG.error("Error opening the file '%s'", boot_log)
        utils.LOG.exception(ex)
    except KeyError, ex:
        utils.LOG.error("Missing key in boot report: import failed")
        utils.LOG.exception(ex)

    return boot_doc


def _parse_boot_from_json(boot_json, database):
    """Parse the boot report from a JSON object.

    :param boot_json: The JSON object.
    :type boot_json: dict
    :return A `models.boot.BootDocument` instance, or None if the JSON cannot
    be parsed correctly.
    """
    boot_doc = None

    try:
        json_pop_f = boot_json.pop
        board = json_pop_f(models.BOARD_KEY)
        job = json_pop_f(models.JOB_KEY)
        kernel = json_pop_f(models.KERNEL_KEY)
        defconfig = json_pop_f(models.DEFCONFIG_KEY)
        defconfig_full = json_pop_f(models.DEFCONFIG_FULL_KEY, defconfig)
        lab_name = json_pop_f(models.LAB_NAME_KEY)
        arch = json_pop_f(models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)

        boot_doc = modbt.BootDocument(
            board, job, kernel, defconfig, lab_name, defconfig_full, arch)
        boot_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)
        _update_boot_doc_from_json(boot_doc, boot_json, json_pop_f)
        _update_boot_doc_ids(boot_doc, database)
    except KeyError, ex:
        utils.LOG.error(
            "Missing key in boot report: import failed"
        )
        utils.LOG.exception(ex)

    return boot_doc


def _update_boot_doc_ids(boot_doc, database):
    """Update boot document job and defconfig IDs references.

    :param boot_doc: The boot document to update.
    :type boot_doc: BootDocument
    :param database: The database connection to use.
    """
    job = boot_doc.job
    kernel = boot_doc.kernel
    defconfig = boot_doc.defconfig

    job_name = models.JOB_DOCUMENT_NAME % {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel
    }
    defconfig_name = models.DEFCONFIG_DOCUMENT_NAME % {
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.DEFCONFIG_KEY: defconfig
    }

    job_doc = utils.db.find_one(
        database[models.JOB_COLLECTION], [job_name], field="name",
        fields=[models.ID_KEY]
    )

    defconfig_doc = utils.db.find_one(
        database[models.DEFCONFIG_COLLECTION], [defconfig_name], field="name",
        fields=[models.ID_KEY]
    )

    if job_doc:
        boot_doc.job_id = job_doc.get(models.ID_KEY, None)
    if defconfig_doc:
        boot_doc.defconfig_id = defconfig_doc.get(models.ID_KEY, None)


def _update_boot_doc_from_json(boot_doc, boot_json, json_pop_f):
    """Update a BootDocument from the provided JSON boot object.

    This function does not return anything, and the BootDocument passed is
    updated from the values found in the provided JSON object.

    :param boot_doc: The BootDocument to update.
    :type boot_doc: `models.boot.BootDocument`.
    :param boot_json: The JSON object from where to take that parameters.
    :type boot_json: dict
    :param json_pop_f: The function used to pop elements out of the JSON object.
    :type json_pop_f: function
    """
    time_d = datetime.timedelta(
        seconds=float(json_pop_f(models.BOOT_TIME_KEY, 0.0))
    )
    boot_doc.time = datetime.datetime(
        1970, 1, 1,
        minute=time_d.seconds / 60,
        second=time_d.seconds % 60,
        microsecond=time_d.microseconds
    )

    boot_doc.status = json_pop_f(
        models.BOOT_RESULT_KEY, models.UNKNOWN_STATUS
    )
    boot_doc.board_instance = json_pop_f(models.BOARD_INSTANCE_KEY, None)
    boot_doc.boot_log = json_pop_f(models.BOOT_LOG_KEY, None)
    boot_doc.boot_log_html = json_pop_f(models.BOOT_LOG_HTML_KEY, None)
    boot_doc.boot_result_description = json_pop_f(
        models.BOOT_RESULT_DESC_KEY, None
    )
    boot_doc.dtb = json_pop_f(models.DTB_KEY, None)
    boot_doc.dtb_addr = json_pop_f(models.DTB_ADDR_KEY, None)
    boot_doc.dtb_append = json_pop_f(models.DTB_APPEND_KEY, None)
    boot_doc.endianness = json_pop_f(models.ENDIANNESS_KEY, None)
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
    boot_doc.retries = json_pop_f(models.BOOT_RETRIES_KEY, 0)
    boot_doc.version = json_pop_f(models.VERSION_KEY, "1.0")
    boot_doc.warnings = json_pop_f(models.BOOT_WARNINGS_KEY, 0)

    boot_doc.metadata = boot_json


def import_all_for_lab(lab_name, base_path=utils.BASE_PATH):
    """Handy function to import all boot logs.

    :param lab_name: The lab name whose boot reports should be imported.
    :type lab_name: str
    :param base_path: Where to start the scan on the hard disk.
    :type base_path: str
    :return A list of BootDocument documents.
    """
    boot_docs = []

    for job in os.listdir(base_path):
        job_dir = os.path.join(base_path, job)

        for kernel in os.listdir(job_dir):
            boot_docs.extend(
                parse_boot_from_disk(job, kernel, lab_name, base_path)
            )

    return boot_docs


def parse_boot_from_disk(job, kernel, lab_name, base_path=utils.BASE_PATH):
    """Traverse the kernel directory and look for boot report logs.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param lab_name: The name of the lab.
    :param base_path: The base path where to start traversing.
    :return A list of documents to be saved, or an empty list.
    """
    docs = []

    job_dir = os.path.join(base_path, job)

    if not utils.is_hidden(job) and os.path.isdir(job_dir):
        kernel_dir = os.path.join(job_dir, kernel)

        if not utils.is_hidden(kernel) and os.path.isdir(kernel_dir):
            for defconfig in os.listdir(kernel_dir):
                defconfig_dir = os.path.join(kernel_dir, defconfig)

                if not utils.is_hidden(defconfig) and \
                        os.path.isdir(defconfig_dir):

                    lab_dir = os.path.join(defconfig_dir, lab_name)
                    if os.path.isdir(lab_dir):
                        docs.extend([
                            _parse_boot_from_file(boot_log)
                            for boot_log in glob.iglob(
                                os.path.join(lab_dir, BOOT_REPORT_PATTERN)
                            )
                            if os.path.isfile(boot_log)
                        ])

    return docs
