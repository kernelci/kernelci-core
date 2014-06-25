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


LOG = get_log()


def find_one(collection,
             values,
             field='_id',
             operator='$in',
             fields=None):
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
    :param fields: The fiels that should be available or excluded from the
        result.
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
        fields=fields,
    )

    return result


def find(collection, limit, skip, spec=None, fields=None, sort=None):
    """Find documents in a collection with optional specified values.

    The `spec` argument is a dictionary of fields and values that should be
    searched in the collection documents. Only the documents matching will be
    returned. By default all documents in the collection will be returned.

    :param collection: The collection where to search.
    :param limit: How many documents to return.
    :type int
    :param skip: How many document to skip from the result.
    :type int
    :param spec: A dictionary object with key-value fields to be matched.
    :type dict
    :param fields: The fields that should be returned or excluded from the
        result.
    :type str, list, dict
    :param sort: Whose fields the result should be sorted on.
    :type list
    :return A list of documents matching the specified values.
    """
    return collection.find(
        limit=limit, skip=skip, fields=fields, sort=sort, spec=spec
    )


def find_and_count(collection, limit, skip, spec=None, fields=None, sort=None):
    """Find all the documents in a collection, and return the total count.

    This will execute two operations: a `find` that will retrieve the documents
    with the specified `limit` and `skip` values, and then a `count` on the
    results found.

    If just `limit` and `skip` are passed, the `count` will return the total
    number of documents in the collection.

    :param collection: The collection where to search.
    :param limit: How many documents to return.
    :type int
    :param skip: How many document to skip from the result.
    :type int
    :param spec: A dictionary object with key-value fields to be matched.
    :type dict
    :param fields: The fields that should be returned or excluded from the
        result.
    :type str, list, dict
    :param sort: Whose fields the result should be sorted on.
    :type list
    :return A dictionary with the result of the `find` operation, the total
        number of documents found, and the `limit` value.
    """
    db_result = collection.find(
        limit=limit, skip=skip, spec=spec, fields=fields, sort=sort
    )
    count = db_result.count()

    return dict(result=db_result, count=count, limit=limit)


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
        the type of each document must be: BaseDocument or a subclass.
    :type list, BaseDocument
    :return 201 if the save has success, 500 in case of an error.
    """
    ret_value = 201

    if not isinstance(documents, types.ListType):
        # Using list() gives error.
        documents = [documents]

    for document in documents:
        if isinstance(document, BaseDocument):
            to_save = document.to_dict()
        else:
            LOG.warn(
                "Cannot save document, it is not of type BaseDocument, got %s",
                type(to_save)
            )
            continue

        try:
            database[document.collection].save(to_save, manipulate=False)
        except OperationFailure, ex:
            LOG.error("Error saving the following document: %s", to_save.name)
            LOG.exception(str(ex))
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
        LOG.error(
            "Error updating the following document: %s", str(document)
        )
        LOG.exception(str(ex))
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
        LOG.error(
            "Error removing the following document: %s", str(spec_or_id)
        )
        LOG.exception(str(ex))
        ret_val = 500

    return ret_val


def aggregate(
        collection, unique, match=None, sort=None, fields=None, limit=None):
    """Perform an aggregate `group` action on the collection.

    If the `sort` parameter is defined, the `sort` action on the aggregate will
    be performed first.

    If `fields` is not defined, the entire document will be returned. This will
    return the last document found based on the sort criteria.

    :param unique: The document attribute on which the `group` action should
        be performed.
    :param match: Which fields the documents should match.
    :param match dict
    :param sort: On which attributes the result should be sorted.
    :type sort list
    :param fields: The fields to return.
    :type fields dict
    :param limit The number of results to return.
    :type limit int, str
    :return A dictionary with the results.
    """

    def _starts_with_dollar(val):
        """Check if a value starts with the dollar sign.

        This is necessary since the aggregate function on MongoDB accepts
        values dollar-escaped.
        """
        if val[0] != '$':
            val = '$' + val
        return val

    # Where the aggregate actions and values will be stored.
    pipeline = []

    if match:
        pipeline.append({
            '$match': match
        })

    # XXX: For strange reasons, sort needs to happen before, and also
    # after grouping, or the resulsts are completely random
    if sort:
        pipeline.append({
            '$sort': {
                k: v for k, v in sort
            }
        })

    group_dict = {
        '$group': {
            '_id': _starts_with_dollar(unique)
        }
    }

    if fields:
        fields = [
            (k, v) for k, v in [
                (key, val)
                for key in fields
                for val in [{'$first': _starts_with_dollar(key)}]
            ]
        ]
    else:
        fields = [('result', {'$first': '$$CURRENT'})]

    group_dict['$group'].update(fields)
    pipeline.append(group_dict)

    # XXX: For strange reasons, sort needs to happen before, and also
    # after grouping, or the resulsts are completely random
    if sort:
        pipeline.append({
            '$sort': {
                k: v for k, v in sort
            }
        })

    # Make sure we return the exact number of elements after grouping them.
    if limit:
        pipeline.append({
            '$limit': limit
        })

    LOG.debug(pipeline)

    result = collection.aggregate(pipeline)

    if result and isinstance(result, types.DictionaryType):
        element = result.get('result', None)

        if all([
                element,
                isinstance(element, types.ListType), len(element) > 0]):
            r_element = element[0]

            if r_element.get('result', None):
                result = [
                    k['result'] for k in [v for v in element]
                ]
            else:
                result = [k for k in element]
        else:
            result = []

    ret_val = None
    if limit:
        ret_val = dict(limit=limit, result=result)
    else:
        ret_val = dict(result=result)

    return ret_val
