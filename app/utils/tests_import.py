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

"""All the necessary functions to import test groups and cases."""

import bson
import copy
import datetime
import types

import models
import models.test_case as mtcase
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


def parse_test_group(group_json, db_options):
    """Parse the test group JSON and retrieve the values to update.

    This is used to update a test group when all its values are empty, but we
    have the build_id, job_id, and/or boot_id.

    Not all values might be retrieved. This function parses the document only
    once and searches for the provided documents only once.

    If only the boot_id is provided, only the field available in that document
    will be update.

    :param group_json: The JSON object.
    :type group_json: dict
    :param db_options: The database connection options.
    :type db_options: dict
    :return A dictionary with the fields-values to update.
    """
    update_doc = {}
    group_pop = group_json.pop

    # The necessary values to link a test group with its job, defconfig
    # and/or boot reports.
    build_id = group_pop(models.BUILD_ID_KEY, None)
    boot_id = group_pop(models.BOOT_ID_KEY, None)
    job_id = group_pop(models.JOB_ID_KEY, None)

    # The set of keys we need to update a test group with to provide search
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
        """Parse the test group JSON object and yield its keys.

        The yielded keys are those with a non-null value.
        """
        for k, v in group_json.iteritems():
            if all([v, v is not None, v != "None", v != "null"]):
                yield k

    good_keys = set([f for f in _get_valid_keys()])
    missing_keys = list(all_keys - good_keys)
    # Save the remove function for later use.
    remove_missing = missing_keys.remove

    # If we have at least one of the referenced documents, and we do not have
    # some of the values that make up a test_group object, look for the
    # document and retrieve the values, then update the test group.
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


def update_test_group(group_json, test_group_id, db_options):
    """Perform update operations on the provided test group.

    Search for missing values based on the other document keys.

    :param group_json: The JSON object containing the test group.
    :type group_json: dict
    :param test_group_id: The ID of the saved test group.
    :type test_group_id: bson.objectid.ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of error; the updated values from the test
    group document as a dictionary.
    """
    ret_val = 200
    update_doc = {}
    local_group = copy.deepcopy(group_json)

    update_doc = parse_test_group(local_group, db_options)
    if update_doc:
        database = utils.db.get_db_connection(db_options)
        ret_val = utils.db.update(
            database[models.TEST_GROUP_COLLECTION],
            {models.ID_KEY: test_group_id}, update_doc)

    return ret_val, update_doc


def import_multi_base(
        import_func, tests_list, group_id, group_name, db_options, **kwargs):
    """Generic function to import test cases list.

    The passed import function must be a function that is able to parse the
    specific test case, and return a 3 values tuple as follows:
    0. The function return value as an integer.
    1. The ID of the saved document, or None if it has not been saved.
    2. An error message if an error occurred, or None.

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

    :param import_func: The function that will be used to import each test
    object as found the test `tests_list` parameter.
    :type import_func: function
    :param tests_list: The list with the test cases to import.
    :type tests_list: list
    :param group_id: The ID of the test group these test objects
    belong to.
    :type group_id: str
    :param group_name: The name of the test group.
    :type group_name: str
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
                test, group_id, group_name, database, db_options, **kwargs)

    for ret_val, doc_id, imp_errors in _yield_tests_import():
        _parse_result(ret_val, doc_id, imp_errors)

    return test_ids, errors


def import_test_case(
        json_obj, group_id, group_name, database, db_options, **kwargs):
    """Parse and save a test case.

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

    :param json_obj: The JSON data structure of the test case to import.
    :type json_obj: dict
    :param group_id: The ID of the test group the test case belongs to.
    :type group_id: bson.objectid.ObjectId
    :param group_name: The name of the test group.
    :type group_name: str
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
        json_group_id = j_get(models.TEST_GROUP_ID_KEY, None)
        group_oid = bson.objectid.ObjectId(group_id)

        json_obj[models.TEST_GROUP_NAME_KEY] = group_name
        if not json_group_id:
            # Inject the group_id value into the data structure.
            json_obj[models.TEST_GROUP_ID_KEY] = group_id
        else:
            if json_group_id == str(group_id):
                json_obj[models.TEST_GROUP_ID_KEY] = group_oid
            else:
                utils.LOG.warning(
                    "Test group ID does not match the provided one")
                # XXX For now, force the group_id value.
                json_obj[models.TEST_GROUP_ID_KEY] = group_oid

        try:
            test_name = j_get(models.NAME_KEY, None)

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
                # reference it in the test group
                else:
                    update_test_group_add_test_case_id(
                        doc_id, group_oid, group_name,
                        db_options)
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
        case_list, group_id, group_name, db_options, **kwargs):
    """Import all the test cases provided.

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

    :param case_list: The list with the test cases to import.
    :type case_list: list
    :param group_id: The ID of the test group these test cases belong to.
    :param group_id: string
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    :return A list with the saved test case IDs or an empty list; a dictionary
    with keys the error codes and value a list of error messages, or an empty
    dictionary.
    """
    return import_multi_base(
        import_test_case,
        case_list, group_id, group_name, db_options, **kwargs)


# TODO: create a separate test_update.py document

def update_test_group_add_sub_group_id(
        group_id, group_name, sub_group_id, db_options):
    """Add sub-group ID to the list in a parent test group and save it.

    :param group_id: The ID of the test group.
    :type case_id: bson.objectid.ObjectId
    :param group_name: The name of the test group.
    :type group_name: str
    :param sub_group_id: The ID of the sub-group.
    :type sub_group_id: bson.objectid.ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """

    ret_val = 200
    errors = {}

    utils.LOG.info(
        "Updating test group '{}' ({}) with sub-group ID {}".format(
            group_name, str(group_id), sub_group_id))
    database = utils.db.get_db_connection(db_options)

    ret_val = utils.db.update(
        database[models.TEST_GROUP_COLLECTION],
        {models.ID_KEY: group_id},
        {models.SUB_GROUPS_KEY: sub_group_id}, operation='$push')
    if ret_val != 200:
        ADD_ERR(
            errors,
            ret_val,
            "Error updating test group '%s' with test group references" %
            (str(group_id))
        )
    return ret_val, errors


def update_test_group_add_test_case_id(
        case_id, group_id, group_name, db_options):
    """Add the test case ID to the list of a a test group and save it.

    :param case_id: The ID of the test case.
    :type case_id: bson.objectid.ObjectId
    :param group_id: The ID of the group.
    :type group_id: bson.objectid.ObjectId
    :param group_name: The name of the test group.
    :type group_name: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """

    ret_val = 200
    errors = {}

    utils.LOG.info(
        "Updating test group '%s' (%s) with test case ID",
        group_name, str(group_id))
    database = utils.db.get_db_connection(db_options)

    ret_val = utils.db.update(
        database[models.TEST_GROUP_COLLECTION],
        {models.ID_KEY: group_id},
        {models.TEST_CASES_KEY: case_id}, operation='$push')
    if ret_val != 200:
        ADD_ERR(
            errors,
            ret_val,
            "Error updating test group '%s' with test case references" %
            (str(group_id))
        )
    return ret_val, errors
