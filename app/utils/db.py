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

"""Collection of mongodb database operations."""

import types

from pymongo.errors import OperationFailure

from models.base import BaseDocument
from utils.log import get_log


log = get_log()


def find_one(collection, values, field='_id', operator='$in'):
    """Search for a specific document.

    The `field' value can be specified, and by default is `_id'.
    The search executed is like:

      collection.find_one({"_id": {"$in": values}})

    :param collection: The collection where to search.
    :param values: The values to search. Can be a list of multiple values.
    :param field: The field where the value should be searched. Defaults to
                  `_id`.
    :param oeprator: The operator used to perform the comparison. Defaults to
                      `$in`.
    :return None or the search result.
    """

    if not isinstance(values, types.ListType):
        if isinstance(values, types.StringTypes):
            values = [values]
        else:
            values = list(values)

    result = collection.find_one(
        {
            field: {operator: values}
        },
    )

    return result


def find(collection, limit, skip):
    """Find all the documents in a collection.

    :param collection: The collection where to search.
    :param limit: How many documents to return.
    :type int
    :param skip: How many documents to skip from the result.
    :type int
    :return A list of documents.
    """
    return collection.find(limit=limit, skip=skip)


def find_and_count(collection, limit, skip):
    """Find all the documents in a collection, and return the total count.

    This will execute two operations: a `find` that will retrieve the documents
    with the specified `limit` and `skip` values, and then a `count` on the
    collection. It returns the total number of documents in the collection.

    :param collection: The collection where to search.
    :param limit: How many documents to return.
    :type int
    :param skip: How many documents to skip from the result.
    :type int
    :return A dictionary with the result of the `find` operation, the total
        number of documents in the collection, and the `limit` value.
    """
    result = dict(
        result=find(collection, limit, skip),
        count=count(collection),
        limit=limit,
    )

    return result


def find_docs(collection, spec, limit, skip, fields=None):
    """Find documents with the specified values.

    The `spec` argument is a dictionary of fields and values that should be
    searched in the collection documents. Only the documents matching will be
    returned.

    :param collection: The collection where to search.
    :param spec: A dictionary object with key-value fields to be matched.
    :type dict
    :param limit: How many documents to return.
    :type int
    :param skip: How many document to skip from the result.
    :type int
    :param fields: The fields that should be returned or excluded from the
                   result.
    :type str, list, dict
    :return A list of documents matching the specified values.
    """
    return collection.find(
        spec=spec, limit=limit, skip=skip, fields=fields
    )


def count_docs(collection, spec):
    """Count all the documents matching the specified values.

    The `spec` argument is a dictionary of fields and values that should be
    searched in the collection documents. Only the documents matching will be
    returned.

    :param collection: The collection where to search.
    :param spec: A dictionary object with key-valu fields to be matched.
    :type dict
    :return The number of documents matching the specified values.
    """
    return collection.find(spec=spec, fields='_id').count()


def count(collection):
    """Count all the documents in a collection.

    :param collection: The collection whose documents should be counted.
    :return The number of documents in the collection.
    """
    return collection.count()


def save(database, documents):
    """Save documents into the database.

    :param database: The database where to save.
    :param documents: The document to save, can be a list or a single document:
                      the type of each document must be: BaseDocument or a
                      subclass.
    :type list, BaseDocument
    :return 201 if the save has success, 500 in case of an error.
    """
    ret_value = 201

    if not isinstance(documents, types.ListType):
        # Using list() gives error.
        documents = [documents]

    for document in documents:
        to_save = None
        if isinstance(document, BaseDocument):
            to_save = document.to_dict()
        else:
            log.warn(
                "Cannot save document, it is not of type BaseDocument, got %s"
                % (type(to_save))
            )
            continue

        try:
            database[document.collection].save(to_save, manipulate=False)
        except OperationFailure, ex:
            log.error("Error saving the following document: %s" % to_save.name)
            log.exception(str(ex))
            ret_value = 500
            break

    return ret_value


def update(collection, spec, document, operation='$set'):
    """Update a document with the provided values.

    The operation is performed on the collection based on the `spec` provided.
    `spec` can specify any document fields. `document` is a dict with the
    key-value to update.

    The default operation performed is `$set`.

    :param spec: The fields that will be matched in the document to update.
    :type dict
    :param document: The key-value to update.
    :type dict
    :param operation: The operation to perform. Be default is `$set`.
    :type str
    :return 200 if the update has success, 500 in case of an error.
    """
    ret_val = 200

    try:
        collection.update(
            spec,
            {
                operation: document,
            }
        )
    except OperationFailure, ex:
        log.error(
            "Error updating the following document: %s" % (str(document))
        )
        log.exception(str(ex))
        ret_val = 500

    return ret_val


def delete(collection, spec_or_id):
    """Remove a document or multiple documents from the collection.

    Use with care: the removed documents cannot be recovered!

    :param collection: The collection where the documents should be removed.
    :param spec_or_id: The `_id` of the document to remove, or a dictionary
                       with the ID to remove.
    :return 200 if the deletion has success, 500 in case of an error.
    """
    ret_val = 200

    try:
        collection.remove(spec_or_id)
    except OperationFailure, ex:
        log.error(
            "Error removing the following document: %s" % (str(spec_or_id))
        )
        log.exception(str(ex))
        ret_val = 500

    return ret_val
