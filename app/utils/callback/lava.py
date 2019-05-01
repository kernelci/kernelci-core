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

import codecs
import errno
import models
import os
import yaml
import json
import urllib2

import utils
import utils.boot
import utils.kci_test
import utils.db
import utils.lava_log_parser
from utils.report.common import DEFAULT_STORAGE_URL

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
    CANCELED: "UNKNOWN",
    CANCELING: "UNKNOWN",
}

TEST_CASE_MAP = {
    models.NAME_KEY: "name",
    models.STATUS_KEY: "result",
    models.INDEX_KEY: "logged",
}

TEST_CASE_NAME_EXTRA = {
    "http-download": ["label"],
    "git-repo-action": ["commit", "path"],
    "test-overlay": ["name"],
    "test-runscript-overlay": ["name"],
    "test-install-overlay": ["name"],
}

META_DATA_MAP_TEST = {
    models.ARCHITECTURE_KEY: "job.arch",
    models.BOARD_KEY: "platform.name",
    models.DEFCONFIG_KEY: "kernel.defconfig_base",
    models.DEFCONFIG_FULL_KEY: "kernel.defconfig",
    models.DEVICE_TYPE_KEY: "device.type",
    models.DTB_KEY: "platform.dtb",
    models.ENDIANNESS_KEY: "kernel.endian",
    models.GIT_BRANCH_KEY: "git.branch",
    models.GIT_COMMIT_KEY: "git.commit",
    models.GIT_DESCRIBE_KEY: "git.describe",
    models.GIT_URL_KEY: "git.url",
    models.INITRD_KEY: "job.initrd_url",
    models.JOB_KEY: "kernel.tree",
    models.KERNEL_KEY: "kernel.version",
    models.KERNEL_IMAGE_KEY: "job.kernel_image",
    models.MACH_KEY: "platform.mach",
    models.VCS_COMMIT_KEY: "git.commit",
    models.IMAGE_TYPE_KEY: "image.type",
    models.PLAN_KEY: "test.plan",
    models.BUILD_ENVIRONMENT_KEY: "job.build_environment",
    models.FILE_SERVER_RESOURCE_KEY: "job.file_server_resource",
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
    models.DEVICE_TYPE_KEY: "device.type",
    models.BUILD_ENVIRONMENT_KEY: "job.build_environment",
    models.FILE_SERVER_RESOURCE_KEY: "job.file_server_resource",
}

BL_META_MAP = {
    "ramdisk_addr": "initrd_addr",
    "kernel_addr": "loadaddr",
    "dtb_addr": "dtb_addr",
}


def _get_job_meta(meta, job_data):
    """Parse the main job meta-data from LAVA

    :param meta: The meta-data to populate.
    :type meta: dictionary
    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param job_data: The map of keys to search for in the JSON and update.
    :type job_data: dict
    """
    meta[models.BOOT_RESULT_KEY] = LAVA_JOB_RESULT[job_data["status"]]
    meta[models.BOARD_INSTANCE_KEY] = job_data["actual_device_id"]


def _get_definition_meta(meta, job_meta, meta_data_map):
    """Parse the job definition meta-data from LAVA

    Parse the meta-data from the LAVA v2 job definition sent with the callback
    and populate the required fields to store in the database.

    :param meta: The meta-data to populate.
    :type meta: dictionary
    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param job_data: The map of keys to search for in the JSON and update.
    :type job_data: dict
    :param meta_data_map: The dict of keys to parse and add in the meta-data.
    :type meta_data_map: dict
    """
    for x, y in meta_data_map.iteritems():
        try:
            meta.update({x: job_meta[y]})
        except (KeyError) as ex:
            utils.LOG.warn("Metadata field {} missing in the job"
                           " result.".format(ex))


def _get_lava_job_meta(meta, boot_meta):
    """Parse the job meta-data from LAVA

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param boot_meta: The boot and auto_login meta-data from the LAVA v2 job.
    :type boot_meta: dictionary
    """
    if boot_meta.get("error_type") == "Infrastructure":
        meta[models.BOOT_RESULT_KEY] = "UNKNOWN"


def _get_lava_boot_meta(meta, boot_meta):
    """Parse the boot and login meta-data from LAVA

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param boot_meta: The boot and auto_login meta-data from the LAVA v2 job.
    :type boot_meta: dictionary
    """
    meta[models.BOOT_TIME_KEY] = boot_meta["duration"]
    extra = boot_meta.get("extra", None)
    if extra is None:
        return
    kernel_messages = []
    for e in extra:
        fail = e.get("fail", None)
        if not fail:
            continue
        if isinstance(fail, str):
            kernel_messages.append(fail)
        else:
            for msg in (f.get("message", None) for f in fail):
                if msg:
                    kernel_messages.append(msg)
    if kernel_messages:
        meta[models.BOOT_WARNINGS_KEY] = len(kernel_messages)


def _get_lava_bootloader_meta(meta, bl_meta):
    """Parse the bootloader meta-data from LAVA

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param bl_meta: The bootloader meta-data from the LAVA v2 job.
    :type bl_meta: dictionary
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
    meta_handlers = {
        'job': _get_lava_job_meta,
        'auto-login-action': _get_lava_boot_meta,
        'bootloader-overlay': _get_lava_bootloader_meta,
    }
    for step in lava:
        handler = meta_handlers.get(step["name"])
        if handler:
            handler(meta, step["metadata"])


def _get_directory_path(meta, base_path):
    """Create the dir_path from LAVA metadata

    Update the metadata with the storage path of the artifacts.
    If possible, use the file_server_resource from the metadata.

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param base_path: The filesystem path where all storage is based
    :type base_path: dict
    """
    file_server_resource = meta.get(models.FILE_SERVER_RESOURCE_KEY)
    if file_server_resource:
        directory_path = os.path.join(
            base_path,
            file_server_resource,
            meta[models.LAB_NAME_KEY])
    else:
        directory_path = os.path.join(
            base_path,
            meta[models.JOB_KEY],
            meta[models.GIT_BRANCH_KEY],
            meta[models.KERNEL_KEY],
            meta[models.ARCHITECTURE_KEY],
            meta[models.DEFCONFIG_FULL_KEY],
            meta[models.BUILD_ENVIRONMENT_KEY],
            meta[models.LAB_NAME_KEY])
    meta[models.DIRECTORY_PATH] = directory_path


def _add_test_log(meta, job_log, suite):
    """Parse and save test logs

    Parse the LAVA v2 log in YAML format and save it as plain text and HTML.

    :param meta: The boot meta-data.
    :type meta: dictionary
    :param log: The kernel log in YAML format.
    :type log: string
    :param base_path: Path to the top-level directory where to store the files.
    :type base_path: string
    :param suite: Test suite name
    :type suite: string
    """
    log = yaml.load(job_log, Loader=yaml.CLoader)

    dir_path = meta[models.DIRECTORY_PATH]

    utils.LOG.info("Generating {} log files in {}".format(suite, dir_path))
    file_name = "-".join([suite, meta[models.BOARD_KEY]])
    files = tuple(".".join([file_name, ext]) for ext in ["txt", "html"])
    meta[models.BOOT_LOG_KEY], meta[models.BOOT_LOG_HTML_KEY] = files
    txt_path, html_path = (os.path.join(dir_path, f) for f in files)

    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    with codecs.open(txt_path, "w", "utf-8") as txt:
        with codecs.open(html_path, "w", "utf-8") as html:
            utils.lava_log_parser.run(log, meta, txt, html)


def _store_lava_json(job_data, meta, base_path=utils.BASE_PATH):
    """ Save the json LAVA v2 callback object

    Save LAVA v2 callback data as json file.

    :param job_data: The JSON data from the LAVA callback.
    :type job_data: dictionary
    :param meta: The boot meta-data.
    :type meta: dictionary
    :param base_path: Path to the top-level directory where to store the files.
    :type base_path: string
    """

    file_name = "-".join(["lava-json", meta[models.BOARD_KEY]])
    file_name = ".".join([file_name, "json"])

    dir_path = meta[models.DIRECTORY_PATH]

    utils.LOG.info("Saving LAVA v2 callback file {} data in {}".format(
        file_name,
        dir_path))

    file_path = os.path.join(dir_path, file_name)

    # Removing the token
    job_data.pop("token", None)

    # Add extra information
    job_data["lab_name"] = meta.get("lab_name")
    job_data["version"] = meta.get("version")
    job_data["boot_log_html"] = meta.get("boot_log_html")

    if not os.path.isdir(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    with open(file_path, "wb") as f:
        f.write(json.dumps(job_data))


def add_boot(job_data, job_meta, lab_name, db_options,
             base_path=utils.BASE_PATH):
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
    :return ObjectId The boot document id.
    """
    ret_code = 201
    doc_id = None
    errors = {}

    utils.LOG.info("Processing LAVA boot data: job {} from {}".format(
        job_data["id"], lab_name))

    meta = {
        models.VERSION_KEY: "1.1",
        models.LAB_NAME_KEY: lab_name,
        models.BOOT_TIME_KEY: "0.0",
    }

    ex = None
    msg = None

    try:
        _get_job_meta(meta, job_data)
        _get_definition_meta(meta, job_meta, META_DATA_MAP_BOOT)
        _get_directory_path(meta, base_path)
        _get_lava_meta(meta, job_data)
        _store_lava_json(job_data, meta)
        _add_test_log(meta, job_data["log"], "boot")
        doc_id = utils.boot.import_and_save_boot(meta, db_options)
    except (yaml.YAMLError, ValueError) as ex:
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
        if errors:
            raise utils.errors.BackendError(errors)

    return doc_id


def _parse_lava_test_data(test_case, test_meta):
    """Parse the test job meta-data for the lava step

    :param test_case: The parsed test case data to be stored in the database.
    :type test_case: dict
    :param test_meta: The test meta-data from the callback.
    :type test_meta: dict
    """
    test_case_name = test_case[models.NAME_KEY]
    extra = TEST_CASE_NAME_EXTRA.get(test_case_name)
    if extra:
        extra_name = [test_case_name]
        for m in test_meta["extra"]:
            for n in extra:
                value = m.get(n)
                if value:
                    extra_name.append(value)
        test_case[models.NAME_KEY] = "-".join(extra_name)


def _add_test_results(group, suite_results, suite_name):
    """Add test results from test suite data to a group.

    Import test results from a LAVA test suite into a group dictionary with the
    list of test cases that are not in any test set.  Test sets are converted
    into sub-groups with the test cases they contain.

    :param group: Test group data.
    :type group: dict
    :param suite_results: Results for the test suite from the callback.
    :type suite_results: dict
    :param suite_name: Name of the test suite being parsed.
    :type suite_name: string
    """
    tests = yaml.load(suite_results, Loader=yaml.CLoader)
    test_cases = []
    test_sets = {}

    for test in reversed(tests):
        test_case = {
            models.VERSION_KEY: "1.1",
            models.TIME_KEY: "0.0",
        }
        test_case.update({k: test[v] for k, v in TEST_CASE_MAP.iteritems()})
        test_meta = test["metadata"]
        if suite_name == "lava":
            _parse_lava_test_data(test_case, test_meta)
        test_set_name = test_meta.get("set")
        if test_set_name:
            test_case_list = test_sets.setdefault(test_set_name, [])
        else:
            test_case_list = test_cases
        test_case[models.INDEX_KEY] = len(test_case_list) + 1
        measurement = test.get("measurement")
        if measurement and measurement != 'None':
            test_case[models.MEASUREMENTS_KEY] = [{
                "value": float(measurement),
                "unit": test["unit"],
            }]
        test_case_list.append(test_case)

    sub_groups = []
    for test_set_name, test_set_cases in test_sets.iteritems():
        sub_group = {
            models.NAME_KEY: test_set_name,
            models.TEST_CASES_KEY: test_set_cases,
        }
        sub_group.update({
            k: group[k] for k in [
                models.ARCHITECTURE_KEY,
                models.BOARD_KEY,
                models.BUILD_ENVIRONMENT_KEY,
                models.DEFCONFIG_FULL_KEY,
                models.DEFCONFIG_KEY,
                models.GIT_BRANCH_KEY,
                models.JOB_KEY,
                models.KERNEL_KEY,
                models.GIT_COMMIT_KEY,
                models.LAB_NAME_KEY,
                models.TIME_KEY,
            ]
        })
        sub_groups.append(sub_group)

    group.update({
        models.TEST_CASES_KEY: test_cases,
        models.SUB_GROUPS_KEY: sub_groups,
    })


def _add_rootfs_info(group, base_path, file_name="build_info.json"):
    """Add rootfs info

    Parse the the JSON file with the information of the rootfs if it's
    available and add its information to the group data.  If the file URL
    matches the local storage server, then read it directly from the file
    system.

    :param group: Test group data.
    :type group: dict
    :param base_path: Path to the top-level directory where files are stored.
    :type base_path: string
    :param file_name: Name of the JSON file with the rootfs info.
    :type file_name: string
    """

    rootfs_url = group.get("initrd")
    if not rootfs_url or rootfs_url == "None":
        return

    try:
        if rootfs_url.startswith(DEFAULT_STORAGE_URL):
            rootfs_url_path = urllib2.urlparse.urlparse(rootfs_url).path
            rootfs_rel_dir = os.path.dirname(rootfs_url_path).lstrip("/")
            json_file = os.path.join(base_path, rootfs_rel_dir, file_name)
            rootfs_info_json = open(json_file)
        else:
            rootfs_top_url = rootfs_url.rpartition("/")[0]
            file_url = "/".join([rootfs_top_url, file_name])
            utils.LOG.info("Downloading rootfs info: {}".format(file_url))
            rootfs_info_json = urllib2.urlopen(file_url)

        rootfs_info = json.load(rootfs_info_json)
        group[models.INITRD_INFO_KEY] = rootfs_info
    except IOError as e:
        utils.LOG.warn("IOError: {}".format(e))
    except ValueError as e:
        utils.LOG.warn("ValueError: {}".format(e))


def add_tests(job_data, job_meta, lab_name, db_options,
              base_path=utils.BASE_PATH):
    """Entry point to be used as an external task.

    This function should only be called by Celery or other task managers.
    Parse the test data from a LAVA v2 job callback and save it along with
    kernel logs.

    :param job_data: The JSON data from the callback.
    :type job_data: dict
    :param lab_name: Name of the LAVA lab that posted the callback.
    :type lab_name: string
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param base_path: Path to the top-level directory where to save files.
    :type base_path: string
    :return The top-level test group document id as ObjectId object.
    """
    ret_code = 201
    group_doc_ids = []
    errors = {}
    ex = None
    msg = None

    utils.LOG.info("Processing LAVA test data: job {} from {}".format(
        job_data["id"], lab_name))

    meta = {
        models.VERSION_KEY: "1.1",
        models.LAB_NAME_KEY: lab_name,
        models.TIME_KEY: "0.0",
    }

    try:
        _get_job_meta(meta, job_data)
        _get_definition_meta(meta, job_meta, META_DATA_MAP_TEST)
        _get_directory_path(meta, base_path)
        _get_lava_meta(meta, job_data)
        plan_name = meta[models.PLAN_KEY]
        _add_test_log(meta, job_data["log"], plan_name)
        _add_rootfs_info(meta, base_path)
        _store_lava_json(job_data, meta)
        # TODO add a test plan entry in the database to group test suites
        for suite_name, suite_results in job_data["results"].iteritems():
            if suite_name != "lava":
                # LAVA adds a prefix index to the test suite names "X_" except
                # for the lava key.  Remove it to get the original name.
                suite_name = suite_name.split("_")[1]
            elif plan_name != "boot":
                continue
            group = dict(meta)
            group[models.NAME_KEY] = suite_name
            _add_test_results(group, suite_results, suite_name)
            ret_code, group_doc_id, err = \
                utils.kci_test.import_and_save_kci_tests(group, db_options)
            utils.errors.update_errors(errors, err)
            group_doc_ids.append(group_doc_id)
    except (yaml.YAMLError, ValueError) as ex:
        ret_code = 400
        msg = "Invalid test data from LAVA callback"
    except (OSError, IOError) as ex:
        ret_code = 500
        msg = "Internal error"
    finally:
        if ex is not None:
            utils.LOG.exception(ex)
        if msg is not None:
            utils.LOG.error(msg)
            utils.errors.add_error(errors, ret_code, msg)
        if errors:
            raise utils.errors.BackendError(errors)

    if not group_doc_ids:
        utils.LOG.warn("No test groups")
        return None

    if len(group_doc_ids) > 1:
        utils.LOG.warn("Discarding extra test group documents")

    return group_doc_ids[0]
