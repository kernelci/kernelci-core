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

"""All the necessary functions to import test sets and test cases."""

import types

import models
import models.test_case as mtcase
import utils
import utils.db


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

    :param case_list: The list with the test cases to import.
    :type case_list: list
    :param test_suite_id: The ID of the test suite these test cases belong to.
    :param test_suite_id: string
    :return A dictionary with keys the error codes and value a list of error
    messages, or an empty dictionary if no errors.
    """
    utils.LOG.info("Importing test cases for test suite '%s'", test_suite_id)

    database = utils.db.get_db_connection(db_options)
    err_results = {}
    res_keys = err_results.viewkeys()

    def _add_err_msg(err_code, err_msg):
        if err_code != 200:
            if err_code in res_keys:
                err_results[err_code].append(err_msg)
            else:
                err_results[err_code] = []
                err_results[err_code].append(err_msg)

    def _yield_test_cases_import():
        for test_case in case_list:
            yield import_test_case(
                test_case, test_suite_id, database, **kwargs)

    [
        _add_err_msg(ret_val, err_msg)
        for ret_val, err_msg in _yield_test_cases_import()
    ]

    return err_results


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

    :param json_case: The JSON data structure of the test case to import.
    :type json_case: dict
    :param test_suite_id: The ID of the test suite these test cases belong to.
    :type test_suite_id: string
    :return 200 if OK, 500 in case of errors, and None or an error message.
    """
    ret_val = 400
    error = None

    if isinstance(json_case, types.DictionaryType):
        j_get = json_case.get
        if j_get(models.TEST_SUITE_ID_KEY, None) is None:
            # Inject the test_suite_id value into the data structure.
            json_case[models.TEST_SUITE_ID_KEY] = test_suite_id

        try:
            test_name = j_get(models.NAME_KEY)
            test_case = mtcase.TestCaseDocument.from_json(json_case)

            if test_case:
                k_get = kwargs.get

                test_case.test_suite_id = test_suite_id
                test_case.test_set_id = k_get(models.TEST_SET_ID_KEY, None)

                utils.LOG.info("Saving test case '%s'", test_name)
                save_val, doc_id = utils.db.save(
                    database, test_case, manipulate=False)

                if save_val == 201:
                    ret_val = 200
                else:
                    ret_val = 500
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

    return ret_val, error
