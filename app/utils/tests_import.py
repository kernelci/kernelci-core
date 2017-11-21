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

"""All the necessary functions to import test suites, sets and cases."""

import bson
import copy
import datetime
import types

import models
import models.test_case as mtcase
import models.test_set as mtset
import utils
import utils.db
import utils.errors

ADD_ERR = utils.errors.add_error
UPDATE_ERR = utils.errors.update_errors


def _get_document_and_update(oid, collection, fields, up_doc, validate_func):
    """Get the document and update the provided data structure.

    Perform a database search on the provided collection, searching for the
    passed `oid` retrieving the provided fields list.

    :param oid: The ID to search.
    :type oid: bson.objectid.ObjectId
    :param collection: The database collection where to search.
    :type collection: MongoClient
    :param fields: The fields to retrieve.
    :type fields: list
    :param up_doc: The document where to store the retrieved fields.
    :type up_doc: dict
    :param validate_func: A function used to validate the retrieved values.
    :type validate_func: function
    """
    doc = utils.db.find_one2(collection, oid, fields=fields)
    if doc:
        up_doc.update(
            {
                k: v
                for k, v in doc.iteritems()
                if validate_func(k, v)
            }
        )


def parse_test_suite(suite_json, db_options):
    """Parse the test suite JSON and retrieve the values to update.

    This is used to update a test suite when all its values are empty, but we
    have the build_id, job_id, and/or boot_id.

    Not all values might be retrieved. This function parses the document only
    once and searches for the provided documents only once.

    If only the boot_id is provided, only the field available in that document
    will be update.

    :param suite_json: The JSON object.
    :type suite_json: dict
    :param db_options: The database connection options.
    :type db_options: dict
    :return A dictionary with the fields-values to update.
    """
    update_doc = {}
    suite_pop = suite_json.pop

    # The necessary values to link a test suite with its job, defconfig
    # and/or boot reports.
    build_id = suite_pop(models.BUILD_ID_KEY, None)
    boot_id = suite_pop(models.BOOT_ID_KEY, None)
    job_id = suite_pop(models.JOB_ID_KEY, None)

    # The set of keys we need to update a test suite with to provide search
    # capabilities based on the values of the job, build and/or boot used.
    all_keys = set([
        models.ARCHITECTURE_KEY,
        models.BOARD_INSTANCE_KEY,
        models.BOARD_KEY,
        models.BOOT_ID_KEY,
        models.BUILD_ID_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY
    ])

    def _get_valid_keys():
        """Parse the test suite JSON object and yield its keys.

        The yielded keys are those with a non-null value.
        """
        for k, v in suite_json.iteritems():
            if all([v, v is not None, v != "None", v != "null"]):
                yield k

    good_keys = set([f for f in _get_valid_keys()])
    missing_keys = list(all_keys - good_keys)
    # Save the remove function for later use.
    remove_missing = missing_keys.remove

    # If we have at least one of the referenced documents, and we do not have
    # some of the values that make up a test_suite object, look for the
    # document and retrieve the values, then update the test suite.
    if all([missing_keys, any([build_id, job_id, boot_id])]):
        def _valid_doc_value(key, value):
            """Check that the value is valid (not null, or empty).

            If the value is valid, remove the key from the ones we need to
            get.

            :param key: The key whose value needs to be checked.
            :type key: string
            :param value: The value to check.
            :type value: string
            :return True or False.
            """
            is_valid = False
            if all([key in all_keys, value]):
                is_valid = True
                remove_missing(key)
            return is_valid

        database = utils.db.get_db_connection(db_options)
        if build_id:
            oid = bson.objectid.ObjectId(build_id)
            update_doc[models.BUILD_ID_KEY] = oid

            _get_document_and_update(
                oid,
                database[models.BUILD_COLLECTION],
                missing_keys,
                update_doc,
                _valid_doc_value
            )

        # If we do not have any more missing keys, do not search further.
        if all([missing_keys, boot_id]):
            oid = bson.objectid.ObjectId(boot_id)
            update_doc[models.BOOT_ID_KEY] = oid

            _get_document_and_update(
                oid,
                database[models.BOOT_COLLECTION],
                missing_keys,
                update_doc,
                _valid_doc_value
            )

        if all([missing_keys, job_id]):
            oid = bson.objectid.ObjectId(job_id)
            update_doc[models.JOB_ID_KEY] = oid

            _get_document_and_update(
                oid,
                database[models.JOB_COLLECTION],
                missing_keys,
                update_doc,
                _valid_doc_value
            )
    else:
        if build_id:
            update_doc[models.BUILD_ID_KEY] = \
                bson.objectid.ObjectId(build_id)
        if boot_id:
            update_doc[models.BOOT_ID_KEY] = \
                bson.objectid.ObjectId(boot_id)
        if job_id:
            update_doc[models.JOB_ID_KEY] = \
                bson.objectid.ObjectId(job_id)

    return update_doc


def update_test_suite(suite_json, test_suite_id, db_options):
    """Perform update operations on the provided test suite.

    Search for missing values based on the other document keys.

    :param suite_json: The JSON object containing the test suite.
    :type suite_json: dict
    :param test_suite_id: The ID of the saved test suite.
    :type test_suite_id: bson.objectid.ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of error; the updated values from the test
    suite document as a dictionary.
    """
    ret_val = 200
    update_doc = {}
    local_suite = copy.deepcopy(suite_json)

    update_doc = parse_test_suite(local_suite, db_options)
    if update_doc:
        database = utils.db.get_db_connection(db_options)
        ret_val = utils.db.update(
            database[models.TEST_SUITE_COLLECTION],
            {models.ID_KEY: test_suite_id}, update_doc)

    return ret_val, update_doc


def import_multi_base(
        import_func, tests_list, suite_id, suite_name, db_options, **kwargs):
    """Generic function to import a test sets or test cases list.

    The passed import function must be a function that is able to parse the
    specific test (either a test set or test case), and return a 3 values tuple
    as follows:
    0. The function return value as an integer.
    1. The ID of the saved document, or None if it has not been saved.
    2. An error message if an error occurred, or None.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * build_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param import_func: The function that will be used to import each test
    object as found the test `tests_list` parameter.
    :type import_func: function
    :param tests_list: The list with the test sets or cases to import.
    :type tests_list: list
    :param suite_id: The ID of the test suite these test objects
    belong to.
    :type suite_id: str
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    :return A list with the saved test objects IDs or an empty list; a
    dictionary with keys the error codes and value a list of error messages,
    or an empty dictionary.
    """
    database = utils.db.get_db_connection(db_options)
    errors = {}
    test_ids = []

    def _parse_result(ret_val, doc_id, imp_errors):
        """Parse the result and its return value.

        :param ret_val: The return value of the test case import.
        :type ret_val: integer
        :param doc_id: The saved document ID.
        :type doc_id: bson.obectid.ObjectId
        :param imp_errors: The error message.
        :type imp_errors: string
        """
        if all([ret_val == 201, doc_id]):
            test_ids.append(doc_id)
        else:
            UPDATE_ERR(errors, imp_errors)

    def _yield_tests_import():
        """Iterate through the test objects to import and return them.

        It will yield the results of the provided import function.
        """
        for test in tests_list:
            yield import_func(
                test, suite_id, suite_name, database, db_options, **kwargs)

    for ret_val, doc_id, imp_errors in _yield_tests_import():
        _parse_result(ret_val, doc_id, imp_errors)

    return test_ids, errors


def import_test_set(
        json_obj, suite_id, suite_name, database, db_options, **kwargs):
    """Parse and save a test set.

    Additional named arguments passed might be (with the exact following
    names):
    * build_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options
    * suite_name

    :param json_obj: The JSON data structure of the test sets to import.
    :type json_obj: dict
    :param suite_id: The ID of the test suite the test set belongs to.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param database: The database connection.
    :param db_options: The database connection options.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; the saved document ID or None;
    a dictionary with error codes and messages.
    """
    ret_val = 400
    errors = {}
    doc_id = None

    if isinstance(json_obj, types.DictionaryType):
        j_get = json_obj.get
        j_pop = json_obj.pop

        json_suite_id = j_get(models.TEST_SUITE_ID_KEY, None)
        cases_list = j_pop(models.TEST_CASE_KEY, [])

        json_obj[models.TEST_SUITE_NAME_KEY] = suite_name
        if not json_suite_id:
            # Inject the suite_id value into the data structure.
            json_obj[models.TEST_SUITE_ID_KEY] = suite_id
        else:
            if json_suite_id == str(suite_id):
                # We want the ObjectId value, not the string.
                json_obj[models.TEST_SUITE_ID_KEY] = suite_id
            else:
                utils.LOG.warning(
                    "Test suite ID does not match the provided one")
                # XXX For now, force the suite_id value.
                json_obj[models.TEST_SUITE_ID_KEY] = suite_id

        try:
            test_name = j_get(models.NAME_KEY, None)
            test_set = mtset.TestSetDocument.from_json(json_obj)

            if test_set:
                test_set.created_on = datetime.datetime.now(
                    tz=bson.tz_util.utc)

                ret_val, doc_id = utils.db.save(
                    database, test_set, manipulate=True)

                if ret_val != 201:
                    err_msg = "Error saving test set '%s'" % test_name
                    utils.LOG.error(err_msg)
                    ADD_ERR(errors, 500, err_msg)
                else:
                    if cases_list:
                        _, imp_err = import_test_cases_from_test_set(
                            doc_id,
                            suite_id,
                            suite_name, cases_list, db_options, **kwargs
                        )
                        UPDATE_ERR(errors, imp_err)
            else:
                ADD_ERR(errors, 400, "Missing mandatory key in JSON data")
        except ValueError, ex:
            ADD_ERR(errors, 400, "Error parsing test set '%s'" % test_name)
            error = (
                "Error parsing test set '{}': {}".format(test_name, ex))
            utils.LOG.error(error)
    else:
        ADD_ERR(errors, 400, "Test set is not valid JSON data")

    return ret_val, doc_id, errors


def import_multi_test_sets(
        set_list, suite_id, suite_name, db_options, **kwargs):
    """Import all the test sets provided.

    Additional named arguments passed might be (with the exact following
    names):
    * build_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param set_list: The list with the test sets to import.
    :type set_list: list
    :param suite_id: The ID of the test suite these test sets belong to.
    :param suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    :return A list with the saved test set IDs or an empty list; a dictionary
    with keys the error codes and value a list of error messages, or an empty
    dictionary.
    """
    return import_multi_base(
        import_test_set, set_list, suite_id, suite_name, db_options, **kwargs)


def import_test_case(
        json_obj, suite_id, suite_name, database, db_options, **kwargs):
    """Parse and save a test case.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * build_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param json_obj: The JSON data structure of the test case to import.
    :type json_obj: dict
    :param suite_id: The ID of the test suite the test case belongs to.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param database: The database connection.
    :param db_options: The database connection options.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; the saved document ID or None;
    a dictionary with error codes and messages.
    """
    ret_val = 400
    errors = {}
    doc_id = None

    if isinstance(json_obj, types.DictionaryType):
        j_get = json_obj.get
        json_suite_id = j_get(models.TEST_SUITE_ID_KEY, None)
        suite_oid = bson.objectid.ObjectId(suite_id)

        json_obj[models.TEST_SUITE_NAME_KEY] = suite_name
        if not json_suite_id:
            # Inject the suite_id value into the data structure.
            json_obj[models.TEST_SUITE_ID_KEY] = suite_id
        else:
            if json_suite_id == str(suite_id):
                json_obj[models.TEST_SUITE_ID_KEY] = suite_oid
            else:
                utils.LOG.warning(
                    "Test suite ID does not match the provided one")
                # XXX For now, force the suite_id value.
                json_obj[models.TEST_SUITE_ID_KEY] = suite_oid

        try:
            test_name = j_get(models.NAME_KEY, None)
            set_id = j_get(models.TEST_SET_ID_KEY, None)
            if set_id:
                set_id = bson.objectid.ObjectId(set_id)
                json_obj[models.TEST_SET_ID_KEY] = set_id
            else:
                json_obj[models.TEST_SET_ID_KEY] = None

            test_case = mtcase.TestCaseDocument.from_json(json_obj)

            if test_case:
                test_case.created_on = datetime.datetime.now(
                    tz=bson.tz_util.utc)
                ret_val, doc_id = utils.db.save(
                    database, test_case, manipulate=True)

                if ret_val != 201:
                    err_msg = "Error saving test case '%s'" % test_name
                    utils.LOG.error(err_msg)
                    ADD_ERR(errors, 500, err_msg)
                # If test case imported correctly
                # reference it in the test suite
                else:
                    update_test_suite_add_test_case_id(
                        doc_id, suite_oid, suite_name,
                        db_options)
                    # and in the test set if it exists
                    if set_id:
                        update_test_set_add_test_case_id(
                            doc_id, set_id, db_options)
            else:
                ADD_ERR(errors, 400, "Missing mandatory key in JSON data")
        except ValueError, ex:
            ADD_ERR(errors, 400, "Error parsing test case '%s'" % test_name)
            error = (
                "Error parsing test case '{}': {}".format(test_name, ex))
            utils.LOG.error(error)
    else:
        ADD_ERR(errors, 400, "Test case is not valid JSON data")

    return ret_val, doc_id, errors


def import_multi_test_cases(
        case_list, suite_id, suite_name, db_options, **kwargs):
    """Import all the test cases provided.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * build_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param case_list: The list with the test cases to import.
    :type case_list: list
    :param suite_id: The ID of the test suite these test cases belong to.
    :param suite_id: string
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    :return A list with the saved test case IDs or an empty list; a dictionary
    with keys the error codes and value a list of error messages, or an empty
    dictionary.
    """
    return import_multi_base(
        import_test_case,
        case_list, suite_id, suite_name, db_options, **kwargs)


def import_test_cases_from_test_set(
        test_set_id, suite_id, suite_name, cases_list, db_options, **kwargs):
    """Import the test cases and update the test set.

    After importing the test cases, save the test set with their IDs.

    :param test_set_id: The ID of the test set.
    :type test_set_id: bson.objectid.ObjectId
    :param suite_id: The ID of the test suite.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param cases_list: The list of test cases to import.
    :type cases_list: list
    :param db_options: The database connection options.
    :type db_options: dict
    """
    ret_val = 200
    errors = {}

    # Inject the test_set_id so that if we have test cases they will use it.
    kwargs[models.TEST_SET_ID_KEY] = test_set_id

    case_ids, errors = import_multi_test_cases(
        cases_list, suite_id, suite_name, db_options, **kwargs)

    if case_ids:
        # Update the test set with the test case IDs.
        database = utils.db.get_db_connection(db_options)
        ret_val = utils.db.update(
            database[models.TEST_SET_COLLECTION],
            {models.ID_KEY: test_set_id},
            {models.TEST_CASE_KEY: case_ids}
        )
        if ret_val != 200:
            error_msg = (
                "Error saving test cases for test set '%s'" % test_set_id)
            ADD_ERR(errors, ret_val, error_msg)
    else:
        ret_val = 500
        error_msg = "No test cases imported for test set '%s'" % test_set_id
        utils.LOG.error(error_msg)
        ADD_ERR(errors, ret_val, error_msg)

    return ret_val, errors

# TODO: create a separate test_update.py document


def update_test_suite_add_test_set_id(
        set_id, suite_id, suite_name, db_options, mail_options):
    """Add the test set ID provided in a test suite.

    This task is linked from the test set post one: It add the
    test set ID as a child of the test suite.

    :param set_id: The ID of the test set.
    :type set_id: bson.objectid.ObjectId
    :param suite_id: The ID of the suite.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    :param mail_options: The email system parameters.
    :type mail_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """

    ret_val = 200
    errors = {}

    utils.LOG.info(
        "Updating test suite '%s' (%s) with test set ID",
        suite_name, str(suite_id))
    database = utils.db.get_db_connection(db_options)

    ret_val = utils.db.update(
        database[models.TEST_SUITE_COLLECTION],
        {models.ID_KEY: suite_id},
        {models.TEST_SET_KEY: set_id}, operation='$push')
    if ret_val != 200:
        ADD_ERR(
            errors,
            ret_val,
            "Error updating test suite '%s' with test set references" %
            (str(suite_id))
        )
    return ret_val, errors


def update_test_suite_add_test_case_id(
        case_id, suite_id, suite_name, db_options):
    """Add the test set ID provided in a test suite.

    This task is linked from the test set post one: It add the
    test set ID as a child of the test suite.

    :param case_id: The ID of the test set.
    :type case_id: bson.objectid.ObjectId
    :param suite_id: The ID of the suite.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """

    ret_val = 200
    errors = {}

    utils.LOG.info(
        "Updating test suite '%s' (%s) with test case ID",
        suite_name, str(suite_id))
    database = utils.db.get_db_connection(db_options)

    ret_val = utils.db.update(
        database[models.TEST_SUITE_COLLECTION],
        {models.ID_KEY: suite_id},
        {models.TEST_CASE_KEY: case_id}, operation='$push')
    if ret_val != 200:
        ADD_ERR(
            errors,
            ret_val,
            "Error updating test suite '%s' with test case references" %
            (str(suite_id))
        )
    return ret_val, errors


def update_test_set_add_test_case_id(
        case_id, set_id, db_options):
    """Add the test set ID provided in a test set.

    This task is linked from the test set post one: It add the
    test set ID as a child of the test set.

    :param case_id: The ID of the test set.
    :type case_id: bson.objectid.ObjectId
    :param set_id: The ID of the set.
    :type set_id: bson.objectid.ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """

    ret_val = 200
    errors = {}

    utils.LOG.info(
        "Updating test set (%s) with test case ID",
        str(set_id))
    database = utils.db.get_db_connection(db_options)

    ret_val = utils.db.update(
        database[models.TEST_SET_COLLECTION],
        {models.ID_KEY: set_id},
        {models.TEST_CASE_KEY: case_id}, operation='$push')
    if ret_val != 200:
        ADD_ERR(
            errors,
            ret_val,
            "Error updating test set '%s' with test case references" %
            (str(set_id))
        )
    return ret_val, errors
