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

"""Container for all the kci_test import related functions."""

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
import models.test_suite as mtest_suite
import models.test_set as mtest_set
import models.test_case as mtest_case
import taskqueue.celery as taskc
import utils
import utils.db
import utils.errors
import utils.tests_import as tests_import

try:  # Py3K compat
    basestring
except NameError:
    basestring = str

# Keys that need to be checked for None or null value.
NON_NULL_KEYS_SUITE = [
    models.BOARD_KEY,
    models.DEFCONFIG_KEY,
    models.JOB_KEY,
    models.KERNEL_KEY,
]

NON_NULL_KEYS_CASE = [
    models.NAME_KEY,
    models.STATUS_KEY,
]

SPEC_TEST_SUITE = {
    models.BOOT_ID_KEY: "boot_id",
    models.NAME_KEY: "name",
}

SPEC_TEST_SET = {
    models.TEST_SUITE_ID_KEY: "test_suite_id",
    models.NAME_KEY: "name",
}

SPEC_TEST_CASE = {
    models.TEST_SUITE_ID_KEY: "test_suite_id",
    models.NAME_KEY: "name",
}

# Local error function.
ERR_ADD = utils.errors.add_error


class TestImportError(Exception):
    """General test import exceptions class."""


class TestValidationError(ValueError, TestImportError):
    """General error for values of test data."""


def save_or_update(doc, spec_map, collection, database, errors):
    """Save or update the document in the database.

    Check if we have a document available in the db, and in case perform an
    update on it.

    :param doc: The document to save.
    :type doc: BaseDocument
    :param collection: The name of the collection to search.
    :type collection: str
    :param database: The database connection.
    :param errors: Where errors should be stored.
    :type errors: dict
    :return The save action return code and the doc ID.
    """
    spec = {}

    fields = [
        models.CREATED_KEY,
        models.ID_KEY,
    ]

    spec.update({x: getattr(doc, y) for x, y in spec_map.iteritems()})

    prev_doc = utils.db.find_one2(
        database[collection], spec, fields=fields)

    if prev_doc:
        doc_get = prev_doc.get
        doc_id = doc_get(models.ID_KEY)
        doc.id = doc_id
        doc.created_on = doc_get(models.CREATED_KEY)

        utils.LOG.info("Updating test document with id '%s'", doc_id)
        ret_val, _ = utils.db.save(database, doc)
    else:
        ret_val, doc_id = utils.db.save(database, doc, manipulate=True)
        utils.LOG.info("New test document with id '%s'", doc_id)

    if ret_val == 500:
        err_msg = (
            "Error saving/updating test report in the database "
            "for '%s (%s)'" %
            (
                doc.name,
                doc.id,
            )
        )
        ERR_ADD(errors, ret_val, err_msg)

    return ret_val, doc_id


def _check_for_null(test_dict, NON_NULL_KEYS):
    """Check if the NON_NULL_KEYS dictionary has values resembling None in its
    mandatory keys.

    Values must be different than:
    - None
    - ""
    - "null"

    :param test_dict: The dictionary to check.
    :type test_dict: dict
    :param NON_NULL_KEYS: The dict of keys to parse and check for non null.
    :type NON_NULL_KEYS: dict
    :raise TestValidationError if any of the keys matches the condition.
    """
    for key in NON_NULL_KEYS:
        val = test_dict.get(key, None)
        if (val is None or
            (isinstance(val, basestring) and
                val.lower() in ('', 'null', 'none'))):
            raise TestValidationError(
                "Invalid value found for mandatory key {!r}: {!r}".format(
                    key, val))


def _get_test_seconds(test_dict):
    """Returns test time in seconds"""
    try:
        test_time_raw = test_dict[models.TIME_KEY]
    except KeyError:
        raise TestValidationError("Test time missing")
    try:
        test_time = float(test_time_raw)
    except ValueError:
        raise TestValidationError(
            "Test time is not a number: {!r}".format(test_time_raw))
    if test_time < 0.0:
        raise TestValidationError("Found negative test time")
    return test_time


def _seconds_as_datetime(seconds):
    """
    Returns seconds encoded as a point in time `seconds` seconds after since
    1970-01-01T00:00:00Z.
    """
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=seconds)


def _update_test_case_doc_from_json(case_doc, test_dict, errors):
    """Update a TestCaseDocument from the provided test dictionary.

    This function does not return anything, the TestCaseDocument passed is
    updated from the values found in the provided JSON object.

    :param case_doc: The TestCaseDocument to update.
    :type case_doc: `models.test_case.TestCaseDocument`.
    :param test_dict: Test case dictionary.
    :type test_dict: dict
    :param errors: Where errors should be stored.
    :type errors: dict
    """

    try:
        seconds = _get_test_seconds(test_dict)
    except TestValidationError as ex:
        seconds = 0.0
        err_msg = "Error reading test time data; defaulting to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    try:
        case_doc.time = _seconds_as_datetime(seconds)
    except OverflowError as ex:
        seconds = 0.0
        err_msg = "Test time value is too large for a time value, default to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    if seconds == 0.0:
        case_doc.time = _seconds_as_datetime(seconds)

    case_doc.definition_uri = test_dict.get(models.DEFINITION_URI_KEY, None)
    case_doc.kvm_guest = test_dict.get(models.KVM_GUEST_KEY, None)
    case_doc.maximum = test_dict.get(models.MAXIMUM_KEY, None)
    case_doc.measurements = test_dict.get(models.MEASUREMENTS_KEY, [])
    case_doc.metadata = test_dict.get(models.METADATA_KEY, None)
    case_doc.minimum = test_dict.get(models.MINIMUM_KEY, None)
    case_doc.samples = test_dict.get(models.SAMPLES_KEY, None)
    case_doc.samples_sqr_sum = test_dict.get(models.SAMPLES_SQUARE_SUM_KEY,
                                             None)
    case_doc.samples_sum = test_dict.get(models.SAMPLES_SUM_KEY, None)
    case_doc.vcs_commit = test_dict.get(models.VCS_COMMIT_KEY, None)
    case_doc.version = test_dict.get(models.VERSION_KEY, "1.0")


def _update_test_case_doc_ids(ts_name, ts_id, case_doc, database):
    """Update test case document test suite IDs references.

    :param ts_name: The test case name
    :type ts_name: str
    :param ts_id: The test case ID
    :type ts_id: str
    :param case_doc: The test case document to update.
    :type case_doc: TestCaseDocument
    :param database: The database connection to use.
    """

    # Make sure the test suite ID provided is correct
    ts_oid = bson.objectid.ObjectId(ts_id)
    test_suite_doc = utils.db.find_one2(database[models.TEST_SUITE_COLLECTION],
                                        ts_oid,
                                        [models.ID_KEY])
    # If exists, update the test case
    if test_suite_doc:
        case_doc.test_suite_name = test_suite_doc.get(models.NAME_KEY, None)
        case_doc.test_suite_id = test_suite_doc.get(models.ID_KEY, None)
    else:
        utils.LOG.error(
            "No test suite document with ID %s found for test case %s",
            ts_oid, case_doc.name)
        return None


def _parse_test_case_from_json(ts_name, ts_id, test_json, database, errors):
    """Parse the test case report from a JSON object.

    :param ts_name: The test case name
    :type ts_name: str
    :param ts_id: The test case ID
    :type ts_id: str
    :param test_json: The JSON object.
    :type test_json: dict
    :param database: The database connection.
    :param errors: Where to store the errors.
    :type errors: dict
    :return A `models.test_case.TestCaseDocument` instance, or None if
    the JSON cannot be parsed correctly.
    """
    if not test_json or not ts_name or not ts_id:
        return None

    try:
        _check_for_null(test_json, NON_NULL_KEYS_CASE)
    except TestValidationError, ex:
        utils.LOG.exception(ex)
        ERR_ADD(errors, 400, str(ex))
        return None

    try:
        name = test_json[models.NAME_KEY]
        status = test_json[models.STATUS_KEY].upper()
    except KeyError, ex:
        err_msg = "Missing mandatory key in test case data"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)
        return None

    test_doc = mtest_case.TestCaseDocument(
        name,
        status)
    test_doc.created_on = datetime.datetime.now(
        tz=bson.tz_util.utc)
    _update_test_case_doc_from_json(test_doc, test_json, errors)
    _update_test_case_doc_ids(ts_name, ts_id, test_doc, database)
    return test_doc


def _update_test_suite_doc_from_json(suite_doc, test_dict, errors):
    """Update a TestSuiteDocument from the provided test dictionary.

    This function does not return anything, the TestSuiteDocument passed is
    updated from the values found in the provided JSON object.

    :param suite_doc: The TestSuiteDocument to update.
    :type suite_doc: `models.test_suite.TestSuiteDocument`.
    :param test_dict: Test suite dictionary.
    :type test_dict: dict
    :param errors: Where errors should be stored.
    :type errors: dict
    """

    try:
        seconds = _get_test_seconds(test_dict)
    except TestValidationError as ex:
        seconds = 0.0
        err_msg = "Error reading test time data; defaulting to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    try:
        suite_doc.time = _seconds_as_datetime(seconds)
    except OverflowError as ex:
        seconds = 0.0
        err_msg = "Test time value is too large for a time value, default to 0"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)

    if seconds == 0.0:
        suite_doc.time = _seconds_as_datetime(seconds)

    suite_doc.arch = test_dict.get(models.ARCHITECTURE_KEY, None)
    suite_doc.board = test_dict.get(models.BOARD_KEY, None)
    suite_doc.board_instance = test_dict.get(models.BOARD_INSTANCE_KEY, None)
    suite_doc.boot_id = test_dict.get(models.BOOT_ID_KEY, None)
    suite_doc.defconfig = test_dict.get(models.DEFCONFIG_KEY, None)
    suite_doc.defconfig_full = test_dict.get(models.DEFCONFIG_FULL_KEY, None)
    suite_doc.git_branch = test_dict.get(models.GIT_BRANCH_KEY, None)
    suite_doc.job = test_dict.get(models.JOB_KEY, None)
    suite_doc.kernel = test_dict.get(models.KERNEL_KEY, None)
    suite_doc.metadata = test_dict.get(models.METADATA_KEY, {})
    suite_doc.vcs_commit = test_dict.get(models.VCS_COMMIT_KEY, None)
    suite_doc.version = test_dict.get(models.VERSION_KEY, "1.0")


def _update_test_suite_doc_ids(suite_doc, database):
    """Update test suite document job and build IDs references.

    :param suite_doc: The test suite document to update.
    :type suite_doc: TestSuiteDocument
    :param database: The database connection to use.
    """
    job = suite_doc.job
    kernel = suite_doc.kernel
    defconfig = suite_doc.defconfig
    defconfig_full = suite_doc.defconfig_full
    arch = suite_doc.arch
    branch = suite_doc.git_branch

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
        suite_doc.job_id = job_doc.get(models.ID_KEY, None)
    else:
        utils.LOG.warn(
            "No job document found for test suite %s-%s-%s-%s (%s)",
            job, branch, kernel, defconfig_full, arch)

    if build_doc:
        doc_get = build_doc.get
        suite_doc.build_id = doc_get(models.ID_KEY, None)

        # In case we do not have the job_id key with the previous search.
        if all([not suite_doc.job_id, doc_get(models.JOB_ID_KEY, None)]):
            suite_doc.job_id = doc_get(models.JOB_ID_KEY, None)
        # Get also git information if we do not have them already,
        if not suite_doc.git_branch:
            suite_doc.git_branch = doc_get(models.GIT_BRANCH_KEY, None)
        if not suite_doc.vcs_commit:
            suite_doc.vcs_commit = doc_get(models.GIT_COMMIT_KEY, None)
    else:
        utils.LOG.warn(
            "No build document found for test suite %s-%s-%s-%s (%s)",
            job, branch, kernel, defconfig_full, arch)


def _parse_test_suite_from_json(test_json, database, errors):
    """Parse the test suite report from a JSON object.

    :param test_json: The JSON object.
    :type test_json: dict
    :param database: The database connection.
    :param errors: Where to store the errors.
    :type errors: dict
    :return A `models.test_suite.TestSuiteDocument` instance, or None if
    the JSON cannot be parsed correctly.
    """
    if not test_json:
        return None

    try:
        _check_for_null(test_json, NON_NULL_KEYS_SUITE)
    except TestValidationError, ex:
        utils.LOG.exception(ex)
        ERR_ADD(errors, 400, str(ex))
        return None

    try:
        name = test_json[models.NAME_KEY]
        lab_name = test_json[models.LAB_NAME_KEY]
    except KeyError, ex:
        err_msg = "Missing mandatory key in test suite data"
        utils.LOG.exception(ex)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)
        return None

    arch = test_json.get(models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)

    if arch not in models.VALID_ARCHITECTURES:
        err_msg = "Invalid architecture found: %s".format(arch)
        utils.LOG.error(err_msg)
        ERR_ADD(errors, 400, err_msg)
        return None

    test_doc = mtest_suite.TestSuiteDocument(
        name,
        lab_name)
    test_doc.created_on = datetime.datetime.now(
        tz=bson.tz_util.utc)
    _update_test_suite_doc_from_json(test_doc, test_json, errors)
    _update_test_suite_doc_ids(test_doc, database)
    return test_doc


def import_and_save_test_sets(test_cases, test_sets,
                              tsu_id, tsu_name,
                              database, errors):
    """Parse the test set report from a JSON object.

    This function parses the test cases reports to find the distinct
    test set names. It creates database entries for each unique set name.
    The test_sets dict is updated accordingly with the IDs of created test
    sets. An operation code is returned for success / error.


    :param test_cases: The JSON object.
    :type test_cases: dict
    :param test_sets: Where to store the test sets references (name & ID).
    :type test_sets: dict
    :param tsu_id: The related test suite ID.
    :type tsu_id: str
    :param tsu_name: The related test suite name.
    :type tsu_name: str
    :param database: The database connection.
    :param errors: Where to store the errors.
    :type errors: dict
    :return the operation code (201 if the save has
    success, 500 in case of an error).
    """
    ret_code = 500
    # Python set(): unordered collections of unique elements
    test_sets_set = set()

    if not test_cases:
        return ret_code
    if not tsu_id or not tsu_name:
        return ret_code

    for test_case in test_cases:
        test_sets_set.add(test_case["set"])

    for test_set_name in test_sets_set:
        test_set_doc = mtest_set.TestSetDocument(
            test_set_name,
            tsu_id)
        test_set_doc.test_suite_name = tsu_name
        test_set_doc.created_on = datetime.datetime.now(
            tz=bson.tz_util.utc)
        if test_set_doc:
            ret_code, test_set_doc_id = \
                save_or_update(test_set_doc, SPEC_TEST_SET,
                               models.TEST_SET_COLLECTION,
                               database, errors)
            # Each test set name = test set id
            test_sets[test_set_name] = test_set_doc_id

            if ret_code == 500:
                err_msg = (
                    "Error saving test set report in the database "
                    "for test suite '%s (%s)'" %
                    (
                        tsu_name,
                        tsu_id,
                    )
                )
                ERR_ADD(errors, ret_code, err_msg)
                return ret_code
            else:
                # Test set imported successfully, update test suite
                tests_import.update_test_suite_add_test_set_id(
                    test_set_doc_id, tsu_id, tsu_name,
                    taskc.app.conf.db_options,
                    taskc.app.conf.mail_options)

        else:
            return 500
    return ret_code


def import_and_save_test_cases(test_cases, test_sets,
                               ts_doc_id, ts_doc_name,
                               database, errors):
    """Import the tests cases report from a JSON object.

    This function returns an operation code based on the import result
    of all the test cases.
    It parses the test_cases JSON, add them to the database and if
    imported successfuly, updates the related test set and suite.

    :param test_cases: The JSON object.
    :type test_cases: dict
    :param test_sets: The JSON object.
    :type test_sets: dict
    :param ts_doc_id: The related test suite ID.
    :type ts_doc_id: str
    :param ts_doc_name: The related test suite name.
    :type ts_doc_name: str
    :param database: The database connection.
    :param errors: Where errors should be stored.
    :type errors: dict
    :return the operation code (201 if the save has
    success, 500 in case of an error).
    """
    ret_code = 500

    if not test_cases:
        return ret_code
    if not ts_doc_id or not ts_doc_name:
        return ret_code

    for test_case in test_cases:
        tc_doc = \
            _parse_test_case_from_json(ts_doc_name, ts_doc_id,
                                       test_case, database, errors)
        if tc_doc:
            tc_doc.test_set_id = test_sets[test_case["set"]]
            ret_code, tc_doc_id = save_or_update(tc_doc, SPEC_TEST_CASE,
                                                 models.TEST_CASE_COLLECTION,
                                                 database, errors)
        if ret_code == 500:
            err_msg = (
                "Error saving test case report in the database "
                "for '%s (%s, %s)'" %
                (
                    tc_doc.name,
                    tc_doc.status,
                    tc_doc.test_suite_id,
                )
            )
            ERR_ADD(errors, ret_code, err_msg)
            return ret_code
        else:
            # Test case imported successfully update test suite
            ret_code, errors = \
                tests_import.update_test_suite_add_test_case_id(
                    tc_doc_id, ts_doc_id, ts_doc_name,
                    taskc.app.conf.db_options)
            # And update test set
            ret_code, errors = \
                tests_import.update_test_set_add_test_case_id(
                    tc_doc_id, tc_doc.test_set_id,
                    taskc.app.conf.db_options)
    return ret_code


def import_and_save_kci_test(test_suite_obj, test_case_obj,
                             db_options, base_path=utils.BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.
    Import and save the test report as found from the parameters in the
    provided JSON object.

    :param test_suite_obj: The JSON object with the values that identify
    the test suite report log.
    :type test_suite_obj: dict
    :param test_case_obj: The JSON object with the values that identify
    the test case report log.
    :type test_case_obj: list
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    """
    ret_code = None
    ts_doc_id = None
    tc_doc_id = None
    test_sets = {}
    errors = {}

    try:
        database = utils.db.get_db_connection(db_options)
        ts_json_copy = copy.deepcopy(test_suite_obj)

        ts_doc = _parse_test_suite_from_json(ts_json_copy, database, errors)
        # If test suite imported correctly
        if ts_doc and not errors:
            ret_code, ts_doc_id = \
                save_or_update(ts_doc, SPEC_TEST_SUITE,
                               models.TEST_SUITE_COLLECTION,
                               database, errors)
            tc_json_copy = copy.deepcopy(test_case_obj)
            # Import and save the test set from the test cases
            ret_code = import_and_save_test_sets(tc_json_copy, test_sets,
                                                 ts_doc_id, ts_doc.name,
                                                 database, errors)
            # Import the test cases
            ret_code = import_and_save_test_cases(tc_json_copy, test_sets,
                                                  ts_doc_id, ts_doc.name,
                                                  database, errors)
            # TODO fix this: need to define a save_to_disk method
            # save_to_disk(ts_doc, test_suite_obj, base_path, errors)
        else:
            utils.LOG.warn("No test suite report imported nor saved")
    except pymongo.errors.ConnectionFailure, ex:
        utils.LOG.exception(ex)
        utils.LOG.error("Error getting database connection")
        ERR_ADD(errors, 500, "Error connecting to the database")

    return ret_code, ts_doc_id, errors
