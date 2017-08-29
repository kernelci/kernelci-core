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
import utils.kci_test
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

DATA_MAP_TEST_CASE = {
    models.NAME_KEY: "name",
    models.STATUS_KEY: "result",
}

META_DATA_MAP_TEST_SUITE = {
    models.DEFCONFIG_KEY: "kernel.defconfig_base",
    models.DEFCONFIG_FULL_KEY: "kernel.defconfig",
    models.GIT_BRANCH_KEY: "git.branch",
    models.VCS_COMMIT_KEY: "git.commit",
    models.KERNEL_KEY: "kernel.version",
    models.JOB_KEY: "kernel.tree",
    models.ARCHITECTURE_KEY: "job.arch",
    models.BOARD_KEY: "platform.name",
    models.NAME_KEY: "test.plan",
}

META_DATA_MAP_BOOT = {
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
    models.MACH_KEY: "platform.mach",
    models.FASTBOOT_KEY: "platform.fastboot",
    models.INITRD_KEY: "job.initrd_url",
    models.BOARD_KEY: "platform.name",
}

BL_META_MAP = {
    "ramdisk_addr": "initrd_addr",
    "kernel_addr": "loadaddr",
    "dtb_addr": "dtb_addr",
}


def _get_test_case_data(meta, tc_data, job_data, META_DATA_MAP):
    """Parse the test definition data from the test suite name

    Parse the data from the LAVA v2 job definition sent with the callback
    and populate the required fields to store in the database.

    :param meta: The test case data to populate.
    :type meta: dictionary
    :param tc_data: The JSON data from the callback.
    :type tc_data: dict
    :param job_data: The map of keys to search for in the JSON and update.
    :type job_data: dict
    :param META_DATA_MAP: The dict of keys to parse and add in the data.
    :type META_DATA_MAP: list
    """
    test_key = None
    found = None
    common_meta = {
        "version": "1.0",
        # Time shoud be passed in the result as well
        "time": "0.0",
    }
    # TODO: Fix ?
    # Kind of workaround because the key for a test will be <number>_test_name
    # Searching for the test plan.
    # But, if the test plan name != test_suite name use the first test suite
    # reported.
    for key in job_data["results"]:
        if "0_" in key:
            test_key = key
        if meta[models.NAME_KEY] in key:
            test_key = key
            found = True
            break

    if not found:
        utils.LOG.warn("Could not find test data for '%s' in lava callback,"
                       " using the first test report available: %s" %
                       (meta[models.NAME_KEY], test_key))

    tests = yaml.load(job_data["results"][test_key],
                      Loader=yaml.CLoader)
    for test in tests:
        test_case = {x: test[y] for x, y in META_DATA_MAP.iteritems()}
        test_case.update(common_meta)
        # If no set is defined make it part of a generic one
        if "set" in test["metadata"]:
            test_case.update({"set": test["metadata"]["set"]})
        else:
            test_case.update({"set": "default"})
        # If measurement add them to the data
        if "measurement" in test["metadata"]:
            value = test["metadata"]["measurement"]
            measurements = {
                "value": float(value),
                "unit": test["metadata"]["units"],
            }
            test_case.update({"measurements": [measurements]})
        tc_data.append(test_case)


def _get_definition_meta(meta, job_data, META_DATA_MAP):
    """Parse the job definition meta-data from LAVA

    Parse the meta-data from the LAVA v2 job definition sent with the callback
    and populate the required fields to store in the database.

    :param meta: The meta-data to populate.
    :type meta: dictionary
    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param job_data: The map of keys to search for in the JSON and update.
    :type job_data: dict
    :param META_DATA_MAP: The dict of keys to parse and add in the meta-data.
    :type META_DATA_MAP: dict
    """
    meta["board_instance"] = job_data["actual_device_id"]
    definition = yaml.load(job_data["definition"], Loader=yaml.CLoader)
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

    utils.LOG.info("Processing LAVA boot data: job {} from {}".format(
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
        _get_definition_meta(meta, job_data, META_DATA_MAP_BOOT)
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


def add_tests(job_data, lab_name, boot_doc_id,
              db_options, base_path=utils.BASE_PATH):
    """Entry point to be used as an external task.

    This function should only be called by Celery or other task managers.
    Parse the test data from a LAVA v2 job callback and save it along with
    kernel logs.

    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param lab_name: Name of the LAVA lab that posted the callback.
    :type lab_name: string
    :param boot_doc_id: The ID of the boot document related to this test suite
    :type boot_doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param base_path: Path to the top-level directory where to save files.
    :type base_path: string
    :return tuple The return code, the boot document id and errors.
    """
    ret_code = 201
    ts_doc_id = None
    errors = {}
    # Test suite metadata
    meta = {
        "version": "1.0",
        "lab_name": lab_name,
        "boot_id": boot_doc_id,
        "time": "0.0",
    }
    # List of test cases data
    tc_data = []

    ex = None
    msg = None

    utils.LOG.info("Processing LAVA test data: job {} from {}".format(
        job_data["id"], lab_name))

    try:
        # Get Test suite definitions
        _get_definition_meta(meta, job_data, META_DATA_MAP_TEST_SUITE)
        # Get Test cases data
        _get_test_case_data(meta, tc_data, job_data, DATA_MAP_TEST_CASE)
        ret_code, ts_doc_id, err = \
            utils.kci_test.import_and_save_kci_test(meta, tc_data, db_options)
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

    return ret_code, ts_doc_id, errors
