# Copyright (C) 2014 Linaro Ltd.
#
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

import types

from pymongo.errors import OperationFailure

from models.base import BaseDocument


def find_one_async(collection, values, field="_id", callback=None):
    """Search for specific document, async version.

    Accepts an extra callback function that will be called with the results.

    The `field' value can be specified, and by default is "_id".
    The search executed is like:

      collection.find_one({"_id": {"$in": values}})

    :param collection: The collection where to search.
    :param values: The values to search. Can be a list of multiple values.
    :param field: The field where the value should be searched. Defaults to
                  "_id".
    :param callback: Function to call with the results.
    :return None or the search result.
    """
    result = find_one(collection, values, field)
    callback(result)


def find_one(collection, values, field="_id"):
    """Search for a specific document.

    The `field' value can be specified, and by default is `_id'.
    The search executed is like:

      collection.find_one({"_id": {"$in": values}})

    :param collection: The collection where to search.
    :param values: The values to search. Can be a list of multiple values.
    :param field: The field where the value should be searched. Defaults to
                  '_id'.
    :return None or the search result.
    """

    if not isinstance(values, types.ListType):
        if isinstance(values, types.StringTypes):
            values = [values]
        else:
            values = list(values)

    result = collection.find_one(
        {
            field: {"$in": values}
        }
    )

    return result


def find_async(collection, limit, skip, callback=None):
    """Find all the documents in a collection, async version.

    Accept and extra `callback' argument.

    :param collection: The mongodb collection to look into.
    :param limit: How many documents to return.
    :type int
    :param skip: How many documents to skip from the mongodb result.
    :type int
    :param callback: Function to call with the results.
    :return A list of documents.
    """
    callback(find(collection, limit, skip))


def find(collection, limit, skip):
    """Find all the documents in a collection.

    :param collection: The mongodb collection to look into.
    :param limit: How many documents to return.
    :type int
    :param skip: How many documents to skip from the mongodb result.
    :type int
    :return A list of documents.
    """
    return collection.find(limit=limit, skip=skip)


def save(database, documents):
    """Save documents into the database.

    :param database: The database where to save.
    :type
    :param documents: The document to save, can be a list or a single document:
                      the type of each document must be: BaseDocument or a
                      subclass.
    :type list, BaseDocument
    :return 200 if the save has success, 500 in case of errors.
    """
    ret_value = 200

    if not isinstance(documents, types.ListType):
        documents = [documents]

    for document in documents:
        to_save = None
        if isinstance(document, BaseDocument):
            to_save = document.to_dict()
        else:
            # TODO log that we cannot save the document.
            continue

        try:
            database[document.collection].save(to_save, manipulate=False)
        except OperationFailure:
            ret_value = 500

    return ret_value
