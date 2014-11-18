#!/usr/bin/python
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

import argparse
import datetime
import time
import sys

import models
import models.boot as mboot
import models.job as mjob
import models.defconfig as mdefconfig
import utils
import utils.db

ZERO_TIME = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)

# Data structures with old ID as the key, and new ID the value.
NEW_JOB_IDS = {}
NEW_DEFCONFIG_IDS = {}


def convert_job_collection(db, limit=0):
    count = db[models.JOB_COLLECTION].find().count()
    utils.LOG.info("Processing %s job documents", count)
    time.sleep(2)

    doc_count = 0
    for document in db[models.JOB_COLLECTION].find(limit=limit):
        doc_get = document.get

        if doc_get("version", None) == "1.0":
            continue
        else:
            doc_count += 1
            job = doc_get("job")
            kernel = doc_get("kernel")

            job_doc = mjob.JobDocument(job, kernel)
            job_doc.version = "1.0"
            job_doc.status = doc_get("status", "UNKNOWN")
            job_doc.created_on = doc_get("created_on")
            job_doc.private = doc_get("private", False)

            metadata = doc_get("metadata", None)
            if metadata:
                meta_get = metadata.get
                job_doc.git_url = meta_get("git_url", None)
                job_doc.git_commit = meta_get("git_commit", None)
                job_doc.git_branch = meta_get("git_branch", None)
                job_doc.git_describe = meta_get("git_describe", None)

            # Delete and save the old doc.
            ret_val = utils.db.delete(db[models.JOB_COLLECTION], doc_get("_id"))
            if ret_val != 200:
                utils.LOG.error(
                    "Error deleting job document %s", doc_get("_id")
                )
                time.sleep(3)
                sys.exit(1)

            ret_val, doc_id = utils.db.save(db, job_doc, manipulate=True)
            if ret_val == 201:
                NEW_JOB_IDS[doc_get("_id")] = doc_id
            else:
                utils.LOG.error(
                    "Error saving new job document for %s", doc_get("_id"))
                time.sleep(3)
                sys.exit(1)

    count = db[models.JOB_COLLECTION].find().count()
    utils.LOG.info("Job documents at the end: %s (%s)", count, doc_count)
    time.sleep(2)


def convert_defconfig_collection(db, limit=0):

    count = db[models.DEFCONFIG_COLLECTION].find().count()
    utils.LOG.info("Processing %s defconfig documents", count)
    time.sleep(2)

    doc_count = 0
    for document in db[models.DEFCONFIG_COLLECTION].find(limit=limit):
        doc_get = document.get

        if doc_get("version", None) == "1.0":
            continue
        else:
            doc_count += 1
            job = doc_get("job")
            kernel = doc_get("kernel")
            defconfig = doc_get("dirname", None) or doc_get("defconfig")

            def_doc = mdefconfig.DefconfigDocument(job, kernel, defconfig)

            def_doc.version = "1.0"
            def_doc.status = doc_get("status", models.UNKNOWN_STATUS)
            def_doc.job_id = NEW_JOB_IDS.get(job + "-" + kernel, None)
            def_doc.dirname = doc_get("dirname", None)
            def_doc.arch = doc_get("arch", None)
            def_doc.created_on = doc_get("created_on")

            def_doc.errors = doc_get("errors", 0)
            if def_doc.errors is None:
                def_doc.errors = 0
            else:
                def_doc.errors = int(def_doc.errors)
            def_doc.warnings = doc_get("warnings", 0)
            if def_doc.warnings is None:
                def_doc.warnings = 0
            else:
                def_doc.warnings = int(def_doc.warnings)
            def_doc.build_time = doc_get("build_time", 0)
            def_doc.modules_dir = doc_get("modules_dir", None)
            def_doc.build_log = doc_get("build_log", None)

            metadata = doc_get("metadata", None)
            if metadata:
                meta_pop = metadata.pop
                meta_get = metadata.get

                if (str(def_doc.errors) != str(meta_get("build_errors")) and
                        meta_get("build_errors") is not None):
                    def_doc.errors = int(meta_pop("build_errors", 0))
                meta_pop("build_errors", 0)

                if (str(def_doc.warnings) != str(meta_get("build_warnings")) and
                        meta_get("build_warnings") is not None):
                    def_doc.warnings = int(meta_pop("build_warnings", 0))
                meta_pop("build_warnings", 0)

                if not def_doc.arch:
                    def_doc.arch = meta_pop("arch", None)
                meta_pop("arch", None)

                def_doc.git_url = meta_pop("git_url", None)
                def_doc.git_branch = meta_pop("git_branch", None)
                def_doc.git_describe = meta_pop("git_describe", None)
                def_doc.git_commit = meta_pop("git_commit", None)
                def_doc.build_platform = meta_pop("build_platform", [])

                if meta_get("build_log", None):
                    def_doc.build_log = meta_get("build_log", None)
                meta_pop("build_log", None)

                if meta_get("build_result", None):
                    result = meta_get("build_result")
                    if result != def_doc.status:
                        def_doc.status = meta_pop("build_result")
                    else:
                        meta_pop("build_result")

                if str(meta_get("build_time")):
                    def_doc.build_time = meta_pop("build_time", 0)
                meta_pop("build_time", None)

                def_doc.dtb_dir = meta_pop("dtb_dir", None)
                def_doc.kernel_config = meta_pop("kernel_config", None)
                def_doc.kernel_image = meta_pop("kernel_image", None)
                def_doc.modules = meta_pop("modules", None)
                def_doc.system_map = meta_pop("system_map", None)
                def_doc.text_offset = meta_pop("text_offset", None)

                if meta_get("modules_dir", None):
                    def_doc.modules_dir = meta_pop("modules_dir")
                meta_pop("modules_dir", None)

                meta_pop("defconfig", None)
                def_doc.metadata = metadata

            ret_val = utils.db.delete(
                db[models.DEFCONFIG_COLLECTION], doc_get("_id")
            )
            if ret_val != 200:
                utils.LOG.error(
                    "Error deleting defconfig document %s", doc_get("_id")
                )
                time.sleep(3)
                sys.exit(1)

            ret_val, doc_id = utils.db.save(db, def_doc, manipulate=True)
            if ret_val == 201:
                NEW_DEFCONFIG_IDS[doc_get("_id")] = doc_id
            else:
                utils.LOG.error(
                    "Error saving new defconfig document for %s",
                    doc_get("_id")
                )
                time.sleep(3)
                sys.exit(1)

    count = db[models.DEFCONFIG_COLLECTION].find().count()
    utils.LOG.info("Defconfig documents at the end: %s (%s)", count, doc_count)
    time.sleep(2)


def convert_boot_collection(db, lab_name, limit=0):

    count = db[models.BOOT_COLLECTION].find().count()
    utils.LOG.info("Processing %s boot documents", count)
    time.sleep(2)

    doc_count = 0
    for document in db[models.BOOT_COLLECTION].find(limit=limit):

        doc_get = document.get

        if doc_get("version", None) == "1.0":
            continue
        else:
            doc_count += 1

            board = doc_get("board")
            job = doc_get("job")
            kernel = doc_get("kernel")
            defconfig = doc_get("defconfig")
            metadata = document.get("metadata", None)

            boot_doc = mboot.BootDocument(
                board, job, kernel, defconfig, lab_name)

            boot_doc.version = "1.0"
            boot_doc.job_id = NEW_JOB_IDS.get(job + "-" + kernel, None)
            boot_doc.defconfig_id = NEW_DEFCONFIG_IDS.get(
                job + "-" + kernel + "-" + defconfig, None
            )
            boot_doc.created_on = doc_get("created_on", None)
            boot_doc.tine = doc_get("time", 0)
            boot_doc.warnings = doc_get("warnings", 0)
            boot_doc.status = doc_get("status", models.UNKNOWN_STATUS)
            boot_doc.boot_log = doc_get("boot_log", None)
            boot_doc.endianness = doc_get("endian", None)
            boot_doc.dtb = doc_get("dtb", None)
            boot_doc.dtb_addr = doc_get("dtb_addr", None)
            boot_doc.initrd_addr = doc_get("initrd_addr", None)
            boot_doc.load_addr = doc_get("load_addr", None)
            boot_doc.retries = doc_get("retries", 0)
            boot_doc.boot_log_html = doc_get("boot_log_html", None)
            boot_doc.boot_log = doc_get("boot_log", None)
            boot_doc.kernel_image = doc_get("kernel_image", None)
            boot_doc.time = doc_get("time", ZERO_TIME)
            boot_doc.dtb_append = doc_get("dtb_append", None)

            if metadata:
                meta_pop = metadata.pop
                boot_doc.fastboot = meta_pop("fastboot", False)
                boot_doc.boot_result_description = meta_pop(
                    "boot_result_description", None)
                if not boot_doc.boot_log_html:
                    boot_doc.boot_log_html = meta_pop("boot_log_html", None)
                if not boot_doc.boot_log:
                    boot_doc.boot_log = meta_pop("boot_log", None)
                boot_doc.dtb_append = meta_pop("dtb_append", None)

                boot_doc.metadata = metadata

            ret_val = utils.db.delete(
                db[models.BOOT_COLLECTION], doc_get("_id"))
            if ret_val != 200:
                utils.LOG.error(
                    "Error deleting boot document %s", doc_get("_id")
                )
                time.sleep(3)
                sys.exit(1)

            ret_val, doc_id = utils.db.save(db, boot_doc, manipulate=True)
            if ret_val != 201:
                utils.LOG.error(
                    "Error saving new boot document for %s",
                    doc_get("_id")
                )
                time.sleep(3)
                sys.exit(1)

    count = db[models.BOOT_COLLECTION].find().count()
    utils.LOG.info("Boot documents at the end: %s (%s)", count, doc_count)
    time.sleep(2)


def _check_func(db):
    """Check some documents if they are ok."""
    for document in db[models.JOB_COLLECTION].find(limit=3):
        print document
    for document in db[models.DEFCONFIG_COLLECTION].find(limit=3):
        print document
    for document in db[models.BOOT_COLLECTION].find(limit=3):
        print document


def main():
    parser = argparse.ArgumentParser(
        description="Convert mongodb data into new model",
        version=0.1
    )
    parser.add_argument(
        "--lab-name", "-n",
        type=str,
        help="The lab name to use for boot reports",
        required=True,
        dest="lab_name"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="The number of documents to process",
        dest="limit"
    )
    args = parser.parse_args()

    lab_name = args.lab_name
    limit = args.limit

    db = utils.db.get_db_connection({})
    convert_job_collection(db, limit)
    convert_defconfig_collection(db, limit)
    convert_boot_collection(db, lab_name, limit)
    _check_func(db)


if __name__ == '__main__':
    main()
