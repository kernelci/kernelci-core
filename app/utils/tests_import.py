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
import utils
import utils.db


def update_test_suite(suite_json, test_suite_id, db_options, **kwargs):
    """Perform update operations on the provided test suite.

    Search for missing values based on the other document keys.

    :param suite_json: The JSON object containing the test suite.
    :type suite_json: dict
    :param test_suite_id: The ID of the saved test suite.
    :type test_suite_id: string
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return
    """
    ret_val = 200
    update_doc = {}
    local_suite = copy.deepcopy(suite_json)

    update_doc = _parse_test_suite(local_suite, db_options)
    if update_doc:
        database = utils.db.get_db_connection(db_options)
        ret_val = utils.db.update(
            database[models.TEST_SUITE_COLLECTION],
            {models.ID_KEY: bson.objectid.ObjectId(test_suite_id)},
            update_doc
        )

    return ret_val, update_doc


def _parse_test_suite(suite_json, db_options):
    """Parse the test suite JSON and retrieve the values to update.

    This is used to update a test suite when all its values are empty, but we
    have the defconfig_id, job_id, and/or boot_id.

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

    defconfig_id = suite_pop(models.DEFCONFIG_ID_KEY, None)
    boot_id = suite_pop(models.BOOT_ID_KEY, None)
    job_id = suite_pop(models.JOB_ID_KEY, None)

    all_keys = set([
        models.ARCHITECTURE_KEY,
        models.BOARD_INSTANCE_KEY,
        models.BOARD_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY
    ])

    def _get_valid_keys():
        """Parse the test suite JSON object and yield its keys.

        The yielded keys are those with a non-null value.
        """
        for k, v in suite_json.iteritems():
            if all([v is not None, v != "", v != "None"]):
                update_doc[k] = v
                yield k

    good_keys = set([f for f in _get_valid_keys()])
    missing_keys = list(all_keys - good_keys)

    # If we have at least one of the referenced documents, and we do not have
    # some of the values that make up a test_suite object, look for the
    # document and retrieve the values, then update the test suite.
    if all([missing_keys, any([defconfig_id, job_id, boot_id])]):
        def _update_missing_keys(key):
            """Remove a key from the needed one when we have a value for it.

            :param key: The key to remove.
            """
            missing_keys.remove(key)

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
                _update_missing_keys(key)
            return is_valid

        database = utils.db.get_db_connection(db_options)
        if defconfig_id:
            oid = bson.objectid.ObjectId(defconfig_id)
            update_doc[models.DEFCONFIG_ID_KEY] = oid

            _get_document_and_update(
                oid,
                database[models.DEFCONFIG_COLLECTION],
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
        if defconfig_id:
            update_doc[models.DEFCONFIG_ID_KEY] = \
                bson.objectid.ObjectId(defconfig_id)
        if boot_id:
            update_doc[models.BOOT_ID_KEY] = \
                bson.objectid.ObjectId(boot_id)
        if job_id:
            update_doc[models.JOB_ID_KEY] = \
                bson.objectid.ObjectId(job_id)

    return update_doc


def _get_document_and_update(oid, collection, fields, up_doc, validate_func):
    """Get the document and update the provided data structure.

    Perform a database search on the provided collection retrieving the
    provided fields list.

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


def import_multi_test_set(set_list, test_suite_id, **kwargs):
    pass


def import_test_set(set_list, test_suite_id, **kwargs):
    pass


def import_multi_test_case(case_list, test_suite_id, db_options, **kwargs):
    """Import all the test cases provided.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * defconfig_id
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
    :param test_suite_id: The ID of the test suite these test cases belong to.
    :param test_suite_id: string
    :param db_options: Options for connecting to the database.
    :type db_options: dict
    :return A list with the saved test case IDs or an empty list; a dictionary
    with keys the error codes and value a list of error messages, or an empty
    dictionary.
    """
    database = utils.db.get_db_connection(db_options)
    err_results = {}
    test_ids = []
    res_keys = err_results.viewkeys()

    def _add_err_msg(err_code, err_msg):
        """Add error code and message to the data structure.

        :param err_code: The error code.
        :type err_code: integer
        :param err_msg: The error messag.
        :"type err_msg: string
        """
        if err_code in res_keys:
            err_results[err_code].append(err_msg)
        else:
            err_results[err_code] = []
            err_results[err_code].append(err_msg)

    def _parse_result(ret_val, doc_id, err_msg):
        """Parse the result and its return value.

        :param ret_val: The return value of the test case import.
        :type ret_val: integer
        :param doc_id: The saved document ID.
        :type doc_id: bson.obectid.ObjectId
        :param err_msg: The error message.
        :type err_msg: string
        """
        if all([ret_val == 201, doc_id]):
            test_ids.append(doc_id)
        else:
            _add_err_msg(ret_val, err_msg)

    def _yield_test_cases_import():
        """Iterate through the test cases to import and return them."""
        for test_case in case_list:
            yield import_test_case(
                test_case, test_suite_id, database, **kwargs)

    [
        _parse_result(ret_val, doc_id, err_msg)
        for ret_val, doc_id, err_msg in _yield_test_cases_import()
    ]

    return test_ids, err_results


def import_test_case(json_case, test_suite_id, database, **kwargs):
    """Parse and save a test case.

    Additional named arguments passed might be (with the exact following
    names):
    * test_set_id
    * defconfig_id
    * job_id
    * job
    * kernel
    * defconfig
    * defconfig_full
    * lab_name
    * board
    * board_instance
    * mail_options

    :param json_case: The JSON data structure of the test case to import.
    :type json_case: dict
    :param test_suite_id: The ID of the test suite these test cases belong to.
    :type test_suite_id: string
    :return 200 if OK, 500 in case of errors; the saved document ID or None;
    an error message in case of error or None.
    """
    ret_val = 400
    error = None
    doc_id = None

    if isinstance(json_case, types.DictionaryType):
        j_get = json_case.get
        if j_get(models.TEST_SUITE_ID_KEY, None) is None:
            # Inject the test_suite_id value into the data structure.
            json_case[models.TEST_SUITE_ID_KEY] = test_suite_id

        try:
            test_name = j_get(models.NAME_KEY, None)
            test_case = mtcase.TestCaseDocument.from_json(json_case)

            if test_case:
                k_get = kwargs.get

                test_case.created_on = datetime.datetime.now(
                    tz=bson.tz_util.utc)
                test_case.test_set_id = k_get(models.TEST_SET_ID_KEY, None)

                utils.LOG.info("Saving test case '%s'", test_name)
                ret_val, doc_id = utils.db.save(
                    database, test_case, manipulate=True)

                if ret_val != 201:
                    error = "Error saving test case '%s'" % test_name
                    utils.LOG.error(error)
            else:
                error = "Missing mandatory key in JSON object"
        except ValueError, ex:
            error = (
                "Error parsing test case '%s': %s" % (test_name, ex.message))
            utils.LOG.exception(ex)
            utils.LOG.error(error)
    else:
        error = "Test case is not a valid JSON object"

    return ret_val, doc_id, error
