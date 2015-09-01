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

"""Common compare methods/functions."""

import pymongo

import models
import utils
import utils.db


def save_delta_doc(json_obj, result, collection, db_options=None):
    """Save the results of a delta calculation.

    :param json_obj: The JSON data used to perform the delta calculation. This
    will be the same data used to perform the search.
    :type json_obj: dict
    :param result: The result of the delta calculation.
    :type result: list
    :param collection: The name of the collection where to save the results.
    :type collection: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    """
    if not db_options:
        db_options = {}

    json_obj["data"] = result

    database = utils.db.get_db_connection(db_options)
    doc_id = None

    try:
        doc_id = database[collection].save(json_obj, manipulate=True)
    except pymongo.errors.OperationFailure:
        utils.LOG.error("Error saving delta doc for %s", collection)

    return doc_id


def search_saved_delta_doc(json_obj, collection, db_options=None):
    """Search for a previously saved delta document.

    The search is performed based on the JSON data passed in the request.
    ID fields are not converted into their ObjectId form.

    :param json_obj: The JSON data to use as a search.
    :type json_obj: dict
    :param collection: The name of the collection where to look.
    :type collection: str
    :param db_options: The databse connection parameters.
    :type db_options: dict
    :return A 2-tuple: the real result, its ID.
    """
    result = None
    if not db_options:
        db_options = {}

    database = utils.db.get_db_connection(db_options)
    result = utils.db.find_one2(database[collection], json_obj)

    if result:
        result = (result["data"], result[models.ID_KEY])

    return result
