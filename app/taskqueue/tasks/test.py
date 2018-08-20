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

"""All test related celery tasks."""

import models
import taskqueue.celery as taskc
import utils
import utils.db
import utils.errors
import utils.tests_import as tests_import

ADD_ERR = utils.errors.add_error


# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=star-args
@taskc.app.task(name="complete-test-suite-import", ignore_result=False)
def complete_test_suite_import(
        suite_json, suite_id, suite_name, db_options):
    """Complete the test suite import.

    First update the test suite references, if what is provided is only the
    *_id values. Then, import the test cases provided.

    :param suite_json: The JSON object with the test suite.
    :type suite_json: dict
    :param suite_id: The ID of the test suite.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary containing the
    new values from the update action.
    """
    ret_val, update_doc = tests_import.update_test_suite(
        suite_json, suite_id, db_options)

    if ret_val != 200:
        utils.LOG.error(
            "Error updating test suite '%s' (%s)", suite_name, suite_id)

    return ret_val, update_doc


@taskc.app.task(
    name="import-cases-from-suite", ignore_result=False, add_to_parent=False)
def import_test_cases_from_test_suite(
        prev_results,
        suite_id, suite_name, tests_list, db_options):
    """Import the test cases provided in a test suite.

    This task is linked from the test suite update one: the first argument is a
    list that contains the return values from the previous task. That argument
    is injected once the task has been completed.

    :param prev_results: Injected value that contain the parent task results.
    :type prev_results: list
    :param suite_id: The ID of the suite.
    :type suite_id: bson.objectid.ObjectId
    :param suite_name: The name of the test suite.
    :type suite_name: str
    :pram tests_list: The list of tests to import.
    :type tests_list: list
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary with errors or an
    empty one.
    """
    ret_val = 200
    errors = {}

    prev_val = prev_results[0]
    other_args = prev_results[1]

    if all([prev_val == 200, suite_id]):
        test_ids, errors = tests_import.import_multi_test_cases(
            tests_list, suite_id, suite_name, db_options, **other_args)

        if test_ids:
            utils.LOG.info(
                "Updating test suite '%s' (%s) with test case IDs",
                suite_name, str(suite_id))
            database = utils.db.get_db_connection(db_options)
            ret_val = utils.db.update(
                database[models.TEST_SUITE_COLLECTION],
                {models.ID_KEY: suite_id}, {models.TEST_CASE_KEY: test_ids})
            if ret_val != 200:
                ADD_ERR(
                    errors,
                    ret_val,
                    "Error updating test suite '%s' with test case "
                    "references" % (str(suite_id))
                )
        else:
            ret_val = 500
    else:
        utils.LOG.warn(
            "Error saving test suite '%s', will not import tests cases",
            suite_name)

    # TODO: handle errors
    return ret_val
