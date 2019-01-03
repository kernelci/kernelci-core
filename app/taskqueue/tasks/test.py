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
import utils.kci_test.regressions

ADD_ERR = utils.errors.add_error


# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=star-args
@taskc.app.task(name="complete-test-group-import", ignore_result=False)
def complete_test_group_import(
        group_json, group_id, group_name, db_options):
    """Complete the test group import.

    First update the test group references, if what is provided is only the
    *_id values. Then, import the test cases provided.

    :param group_json: The JSON object with the test group.
    :type group_json: dict
    :param group_id: The ID of the test group.
    :type group_id: bson.objectid.ObjectId
    :param group_name: The name of the test group.
    :type group_name: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return 200 if OK, 500 in case of errors; a dictionary containing the
    new values from the update action.
    """
    ret_val, update_doc = tests_import.update_test_group(
        group_json, group_id, db_options)

    if ret_val != 200:
        utils.LOG.error(
            "Error updating test group '%s' (%s)", group_name, group_id)

    return ret_val, update_doc


@taskc.app.task(
    name="import-cases-from-group", ignore_result=False, add_to_parent=False)
def import_test_cases_from_test_group(
        prev_results,
        group_id, group_name, tests_list, db_options):
    """Import the test cases provided in a test group.

    This task is linked from the test group update one: the first argument is a
    list that contains the return values from the previous task. That argument
    is injected once the task has been completed.

    :param prev_results: Injected value that contain the parent task results.
    :type prev_results: list
    :param group_id: The ID of the group.
    :type group_id: bson.objectid.ObjectId
    :param group_name: The name of the test group.
    :type group_name: str
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

    if all([prev_val == 200, group_id]):
        test_ids, errors = tests_import.import_multi_test_cases(
            tests_list, group_id, group_name, db_options, **other_args)

        if test_ids:
            utils.LOG.info(
                "Updating test group '%s' (%s) with test case IDs",
                group_name, str(group_id))
            database = utils.db.get_db_connection(db_options)
            ret_val = utils.db.update(
                database[models.TEST_GROUP_COLLECTION],
                {models.ID_KEY: group_id}, {models.TEST_CASES_KEY: test_ids})
            if ret_val != 200:
                ADD_ERR(
                    errors,
                    ret_val,
                    "Error updating test group '%s' with test case "
                    "references" % (str(group_id))
                )
        else:
            ret_val = 500
    else:
        utils.LOG.warn(
            "Error saving test group '%s', will not import tests cases",
            group_name)

    # TODO: handle errors
    return ret_val


@taskc.app.task(name="test-regressions")
def find_regression(group_id):
    """Find test case regressions in the given test group.

    Run this function in a Celery task to find any test case regressions for
    the given test group document ID, recursively through all sub-groups.

    :param group_id: Test group document object ID.
    :return tuple 200 if OK, 500 in case of errors; a list with created test
    regression document ids
    """
    return utils.kci_test.regressions.find(group_id, taskc.app.conf.db_options)
