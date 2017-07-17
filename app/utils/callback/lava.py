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

import errno
import models
import os
import yaml

import utils
import utils.boot
import utils.db
import utils.lava_log_parser

# copied from lava-server/lava_scheduler_app/models.py
SUBMITTED = 0
RUNNING = 1
COMPLETE = 2
INCOMPLETE = 3
CANCELED = 4
CANCELING = 5

LAVA_JOB_RESULT = {
    COMPLETE: "PASS",
    INCOMPLETE: "FAIL",
}

META_DATA_MAP = {
    models.DEFCONFIG_KEY: "kernel.defconfig_base",
    models.DEFCONFIG_FULL_KEY: "kernel.defconfig",
    models.GIT_BRANCH_KEY: "git.branch",
    models.GIT_COMMIT_KEY: "git.commit",
    models.GIT_DESCRIBE_KEY: "git.describe",
    models.GIT_URL_KEY: "git.url",
    models.KERNEL_KEY: "kernel.version",
    models.KERNEL_IMAGE_KEY: "job.kernel_image",
    models.ENDIANNESS_KEY: "kernel.endian",
    models.JOB_KEY: "kernel.tree",
    models.ARCHITECTURE_KEY: "job.arch",
    models.DTB_KEY: "platform.dtb",
    models.FASTBOOT_KEY: "platform.fastboot",
    models.INITRD_KEY: "job.initrd_url",
    models.BOARD_KEY: "device.type",
}

BL_META_MAP = {
    "ramdisk_addr": "initrd_addr",
    "kernel_addr": "loadaddr",
    "dtb_addr": "dtb_addr",
}


def _get_definition_meta(meta, job_data):
    """Parse the job definition meta-data from LAVA

    Parse the meta-data from the LAVA v2 job definition sent with the callback
    and populate the required fields to store in the database.

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param job_data: The JSON data from the callback.
    :type job_data: dict

    """
    meta["board_instance"] = job_data["actual_device_id"]
    definition = yaml.load(job_data["definition"], Loader=yaml.CLoader)
    meta["mach"] = definition["device_type"]
    job_meta = definition["metadata"]
    meta.update({x: job_meta[y] for x, y in META_DATA_MAP.iteritems()})


def _get_lava_boot_meta(meta, boot_meta):
    """Parse the boot and login meta-data from LAVA

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param boot_meta: The boot and auto_login meta-data from the LAVA v2 job.
    :type meta: dictionary
    """
    meta["boot_time"] = boot_meta["duration"]
    extra = boot_meta.get("extra", None)
    if extra is None:
        return
    kernel_messages = []
    for e in extra:
        fail = e.get("fail", None)
        if fail is not None:
            for f in fail:
                msg = f.get("message", None)
                if msg:
                    kernel_messages.append(msg)
    if kernel_messages:
        meta["boot_warnings"] = kernel_messages


def _get_lava_bootloader_meta(meta, bl_meta):
    """Parse the bootloader meta-data from LAVA

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param bl_meta: The bootloader meta-data from the LAVA v2 job.
    :type meta: dictionary
    """
    extra = bl_meta.get("extra", None)
    if extra is None:
        return
    for e in extra:
        for k, v in e.iteritems():
            meta_key = BL_META_MAP.get(k, None)
            if meta_key:
                meta[meta_key] = v


def _get_lava_meta(meta, job_data):
    """Parse the meta-data from LAVA

    Go through the LAVA meta-data and extract the fields needed to create a
    boot entry in the database.

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param job_data: The JSON data from the callback.
    :type job_data: dict
    """
    lava = yaml.load(job_data["results"]["lava"], Loader=yaml.CLoader)
    for step in lava:
        if step["name"] == "auto-login-action":
            _get_lava_boot_meta(meta, step["metadata"])
        elif step["name"] == "bootloader-overlay":
            _get_lava_bootloader_meta(meta, step["metadata"])


def _add_boot_log(meta, log, base_path):
    """Parse and save kernel logs

    Parse the kernel boot log in YAML format from a LAVA v2 job and save it as
    plain text and HTML.

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param log: The kernel log in YAML format.
    :type log: string
    :param base_path: Path to the top-level directory where to store the files.
    :type base_path: string
    """
    log = yaml.load(log, Loader=yaml.CLoader)

    dir_path = os.path.join(
        base_path,
        meta["job"],
        meta["git_branch"],
        meta["kernel"],
        meta["arch"],
        meta["defconfig_full"],
        meta["lab_name"])
    utils.LOG.info("Generating boot log files in {}".format(dir_path))
    file_name = "-".join(["boot", meta["board"]])
    files = tuple(".".join([file_name, ext]) for ext in ["txt", "html"])
    meta["boot_log"], meta["boot_log_html"] = files
    txt_path, html_path = (os.path.join(dir_path, f) for f in files)

    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    with open(txt_path, "w") as txt, open(html_path, "w") as html:
        utils.lava_log_parser.run(log, meta, txt, html)


def add_boot(job_data, lab_name, db_options, base_path=utils.BASE_PATH):
    """Entry point to be used as an external task.

    This function should only be called by Celery or other task managers.
    Parse the boot data from a LAVA v2 job callback and save it along with
    kernel logs.

    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param lab_name: Name of the LAVA lab that posted the callback.
    :type lab_name: string
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param base_path: Path to the top-level directory where to save files.
    :type base_path: string
    :return tuple The return code, the boot document id and errors.
    """
    ret_code = 201
    doc_id = None
    errors = {}

    utils.LOG.info("Processing LAVA data: job {} from {}".format(
        job_data["id"], lab_name))

    meta = {
        "version": "1.1",
        "lab_name": lab_name,
        "boot_time": "0.0",
    }

    ex = None
    msg = None

    try:
        meta["boot_result"] = LAVA_JOB_RESULT[job_data["status"]]
        _get_definition_meta(meta, job_data)
        _get_lava_meta(meta, job_data)
        _add_boot_log(meta, job_data["log"], base_path)
        ret_code, doc_id, err = \
            utils.boot.import_and_save_boot(meta, db_options)
        utils.errors.update_errors(errors, err)
    except (yaml.YAMLError, ValueError, KeyError) as ex:
        ret_code = 400
        msg = "Invalid LAVA data"
    except (OSError, IOError) as ex:
        ret_code = 500
        msg = "Internal error"
    finally:
        if ex is not None:
            utils.LOG.exception(ex)
        if msg is not None:
            utils.LOG.error(msg)
            utils.errors.add_error(errors, ret_code, msg)

    return ret_code, doc_id, errors
