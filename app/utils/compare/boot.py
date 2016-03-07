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

"""Perform boot delta calculations.

Boot delta calculations are performed by returining the database results
(almost) as is, with a few calculations done here locally.
"""

import bson

import models
import models.compare
import utils.compare.common
import utils.db
import utils.errors
import utils.validator


ADD_ERR = utils.errors.add_error


# pylint: disable=too-many-branches
def search_and_compare(json_obj, compare_to, errors, db_options):
    """Search for the baseline and compare documents.

    Execute any comparison function available and return the results in a new
    data structure.

    :param json_obj: The document with the comparison data.
    :type json_obj: dict
    :param errors: The errors data structure.
    :type errors: dict
    :param compare_to: The list of compare targets. Each target is a dict.
    :type compare_to: list
    :param db_options: The database connection options.
    :type db_options: dict
    :return A 2-tuple: the status code and the result as a list.
    """
    compare_data = {}
    database = utils.db.get_db_connection(db_options)
    result = []
    status = 200

    def _find(to_search):
        """Internally used to search and update the document.

        Special case of a comparison since we only need to extract all the
        documents and provide them as is, except for some minor updates.

        :param to_search: The data to search for.
        :type to_search: dict
        :return A 2-tuple: the status code and the found document.
        """
        doc = {}
        spec = {}
        status_code = 200

        t_get = to_search.get
        build_id = t_get(models.BOOT_ID_KEY, None)

        if build_id:
            try:
                doc_id = bson.objectid.ObjectId(build_id)
                spec = {models.ID_KEY: doc_id}
            except bson.errors.InvalidId:
                status_code = 400
                ADD_ERR(errors, 400, "Provided build ID value is not valid")
        else:
            spec = {
                models.ARCHITECTURE_KEY: t_get(models.ARCHITECTURE_KEY),
                models.BOARD_KEY: t_get(models.BOARD_KEY),
                models.DEFCONFIG_FULL_KEY: t_get(models.DEFCONFIG_FULL_KEY),
                models.JOB_KEY: t_get(models.JOB_KEY),
                models.KERNEL_KEY: t_get(models.KERNEL_KEY),
                models.LAB_NAME_KEY: t_get(models.LAB_NAME_KEY)
            }

        if spec:
            doc = database[models.BOOT_COLLECTION].find_one(spec)

            if not doc:
                status_code = 404
                ADD_ERR(errors, 404, "No data found")

        return status_code, doc

    status, baseline = _find(json_obj)
    if all([status == 200, baseline]):
        compare_data[models.BASELINE_KEY] = baseline

        compare_result = []
        for compare_doc in compare_to:
            is_valid, err_msg = utils.validator.is_valid_json(
                compare_doc, models.compare.BOOT_COMPARE_VALID_KEYS)

            if is_valid:
                status, compared = _find(compare_doc)

                if all([status == 200, compared]):
                    compare_result.append(compared)
                else:
                    break
            else:
                status = 400
                ADD_ERR(errors, 400, err_msg)
                break
        else:
            status = 200
            compare_data[models.COMPARE_TO_KEY] = compare_result
            result.append(compare_data)

    return status, result


# pylint: disable=too-many-locals
def execute_delta(json_obj, db_options=None):
    """Execute the build delta calculations.

    :param json_obj: The JSON object containing the data to start the delta.
    :type json_obj: dict
    :param db_options: The database connection options.
    :type db_options: dict
    :return A 3-tuple: The status code (200 OK), the list of result and an
    error data structure.
    """
    doc_id = None
    errors = {}
    result = []
    status = 200

    if not db_options:
        db_options = {}

    j_get = json_obj.get

    job = j_get(models.JOB_KEY, None)
    kernel = j_get(models.KERNEL_KEY, None)
    defconfig_full = j_get(models.DEFCONFIG_FULL_KEY, None)
    arch = j_get(models.ARCHITECTURE_KEY, None)
    board = j_get(models.BOARD_KEY, None)
    lab_name = j_get(models.LAB_NAME_KEY, None)
    compare_to = j_get(models.COMPARE_TO_KEY, [])
    boot_id = j_get(models.BOOT_ID_KEY, None)

    if all([not boot_id,
            any([not job,
                 not kernel,
                 not defconfig_full, not arch, not board, not lab_name])]):
        status = 400
        ADD_ERR(errors, 400, "Missing mandatory data to perform a comparison")
    elif not compare_to:
        status = 400
        ADD_ERR(errors, 400, "No data provided to compare to")
    else:
        # Need to make sure that when the compare_to dictionaries come in they
        # have determined sorting, or we might have POST requests with exactly
        # the same data that create multiple identical results (due to the
        # fact that the keys order in a dictionary is not deterministic).
        # Create a list of ordered tuples.
        compare_to_sorted = []
        comp_extend = compare_to_sorted.extend
        for element in compare_to:
            element_items = element.items()
            element_items.sort()
            comp_extend(element_items)
        json_obj[models.COMPARE_TO_KEY] = compare_to_sorted

        # First search for any saved results.
        saved = utils.compare.common.search_saved_delta_doc(
            json_obj, models.BOOT_DELTA_COLLECTION, db_options)

        if saved:
            result, doc_id = saved[0], saved[1]
        else:
            status, result = search_and_compare(
                json_obj, compare_to, errors, db_options)

            if any([status == 201, status == 200]):
                doc_id = utils.compare.common.save_delta_doc(
                    json_obj,
                    result, models.BOOT_DELTA_COLLECTION, db_options)

    return status, result, doc_id, errors
