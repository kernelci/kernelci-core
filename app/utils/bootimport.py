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

import bson
import datetime
import glob
import json
import os
import pymongo
import re

import models
import models.boot as modbt
import utils
import utils.db as db

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
    :param base_path: The base path where to start looking for the boot log
    file. It defaults to: /var/www/images/kernel-ci.
    """
    database = db.get_db_connection(db_options)
    docs = parse_boot_from_json(json_obj, base_path)

    if docs:
        db.save(database, docs)
    else:
        utils.LOG.info("No boot log imported")


def parse_boot_from_json(json_obj, base_path=utils.BASE_PATH):
    """Parse boot log file from a JSON object.

    The provided JSON object, a dict-like object, should contain at least the
    `job` and `kernel` keys.

    :param json_obj: A dict-like object that should contain the keys `job` and
    :param base_path: The base path where to start looking for the boot log
        file. It defaults to: /var/www/images/kernel-ci.
    :return A list with all the `BootDocument`s.
    """
    # FIXME: need to add lab_id.
    job = json_obj[models.JOB_KEY]
    kernel = json_obj[models.KERNEL_KEY]

    return _parse_boot(job, kernel, base_path)


def _parse_boot(job, kernel, base_path=utils.BASE_PATH):
    """Traverse the kernel directory and look for boot report logs.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
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
                    docs.extend([
                        _parse_boot_log(boot_log, job, kernel, defconfig)
                        for boot_log in glob.iglob(
                            os.path.join(defconfig_dir, BOOT_REPORT_PATTERN)
                        )
                        if os.path.isfile(boot_log)
                    ])

    return docs


def _parse_boot_log(boot_log, job, kernel, defconfig):
    """Read and parse the actual boot report.

    :param boot_log: The path to the boot report.
    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param defconfig: The name of the defconfig.
    :return A `BootDocument` object.
    """

    utils.LOG.info("Parsing boot log '%s'", os.path.basename(boot_log))

    boot_json = None
    boot_doc = None

    with open(boot_log) as read_f:
        boot_json = json.load(read_f)

    if boot_json:
        dtb = boot_json.pop(models.DTB_KEY, None)

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

        # FIXME: need to pass the lab_id.
        boot_doc = modbt.BootDocument(board, job, kernel, defconfig)
        boot_doc.created_on = datetime.datetime.fromtimestamp(
            os.stat(boot_log).st_mtime, tz=bson.tz_util.utc)

        time_d = datetime.timedelta(
            seconds=float(boot_json.pop(models.BOOT_TIME_KEY, 0.0))
        )
        boot_time = datetime.datetime(
            1970, 1, 1,
            minute=time_d.seconds / 60,
            second=time_d.seconds % 60,
            microsecond=time_d.microseconds
        )

        json_pop = boot_json.pop
        boot_doc.time = boot_time
        boot_doc.status = json_pop(
            models.BOOT_RESULT_KEY, models.UNKNOWN_STATUS
        )
        boot_doc.warnings = json_pop(models.BOOT_WARNINGS_KEY, "0")
        boot_doc.boot_log = json_pop(models.BOOT_LOG_KEY, None)
        boot_doc.initrd_addr = json_pop(models.INITRD_ADDR_KEY, None)
        boot_doc.load_addr = json_pop(models.BOOT_LOAD_ADDR_KEY, None)
        boot_doc.kernel_image = json_pop(models.KERNEL_IMAGE_KEY, None)
        boot_doc.dtb_addr = json_pop(models.DTB_ADDR_KEY, None)
        boot_doc.endianness = json_pop(models.ENDIANNESS_KEY, None)
        boot_doc.boot_log_html = json_pop(models.BOOT_LOG_HTML_KEY, None)
        boot_doc.fastboot = json_pop(models.FASTBOOT_KEY, None)
        boot_doc.boot_result_description = json_pop(
            models.BOOT_RESULT_DESC_KEY, None
        )
        boot_doc.retries = json_pop(models.BOOT_RETRIES_KEY, None)
        boot_doc.dtb = dtb

        boot_doc.metadata = boot_json
    else:
        utils.LOG.error(
            "Boot log '%s' does not contain JSON data",
            os.path.basename(boot_log)
        )

    return boot_doc


def _import_all(base_path=utils.BASE_PATH):
    """Handy function to import all boot logs."""
    boot_docs = []

    for job in os.listdir(base_path):
        job_dir = os.path.join(base_path, job)

        for kernel in os.listdir(job_dir):
            boot_docs.extend(_parse_boot(job, kernel, base_path))

    return boot_docs


# pylint: disable=invalid-name
if __name__ == '__main__':
    connection = pymongo.MongoClient()
    loc_db = connection[models.DB_NAME]

    all_docs = _import_all()
    db.save(loc_db, all_docs)

    connection.disconnect()
