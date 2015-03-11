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

import pymongo
import pymongo.errors
import types

import models
import models.base as mbase
import utils

DB_CONNECTION = None


def get_db_connection(db_options):
    """Retrieve a mongodb database connection.

    :params db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A mongodb database instance.
    """
    global DB_CONNECTION

    if DB_CONNECTION is None:
        db_options_get = db_options.get

        db_host = db_options_get("dbhost", utils.DEFAULT_MONGODB_URL)
        db_port = db_options_get("dbport", utils.DEFAULT_MONGODB_PORT)
        db_pool = db_options.get("dbpool", utils.DEFAULT_MONGODB_POOL)

        db_user = db_options_get("dbuser", "")
        db_pwd = db_options.get("dbpassword", "")

        DB_CONNECTION = pymongo.MongoClient(
            host=db_host, port=db_port, max_pool_size=db_pool
        )[models.DB_NAME]

        if all([db_user, db_pwd]):
            DB_CONNECTION.authenticate(db_user, password=db_pwd)

    return DB_CONNECTION


def find_one(collection,
             value,
             field="_id",
             operator="$in",
             fields=None):
    """Search for a specific document.

    The `field' value can be specified, and by default is `_id'.
    The search executed is like:

      collection.find_one({"_id": {"$in": value}})

    :param collection: The collection where to search.
    :param value: The value to search. It has to be of the appropriate type for
    the operator in use. If using the default operator `$in`, it must be a
    list.
    :param field: The field where the value should be searched. Defaults to
        `_id`.
    :param oeprator: The operator used to perform the comparison. Defaults to
        `$in`.
    :param fields: The fiels that should be available or excluded from the
        result.
    :return None or the search result as a dictionary.
    """
    result = None
    if all([operator == '$in', not isinstance(value, types.ListType)]):
        utils.LOG.error(
            "Provided value (%s) is not of type list, got: %s",
            value,
            type(value)
        )
    else:
        result = collection.find_one(
            {
                field: {operator: value}
            },
            fields=fields,
        )

    return result


def find_one2(collection, spec_or_id, fields=None):
    """Search for a single document.

    This is different from `find_one` in that it accepts a more generic `spec`
    data structure instead of creating one on the fly.

    :param collection: The collection where to search.
    :param spec_or_id: A `spec` data structure or the document id.
    :param fields: The fiels that should be available or excluded from the
    result.
    :return None or the search result as a dictionary.
    """
    return collection.find_one(spec_or_id, fields=fields)


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
        limit=limit, skip=skip, fields=fields, sort=sort, spec=spec)


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
    :return The search result and the total count.
    """
    db_result = collection.find(
        spec=spec, limit=limit, skip=skip, fields=fields, sort=sort)
    res_count = db_result.count()

    return db_result, res_count


def count(collection):
    """Count all the documents in a collection.

    :param collection: The collection whose documents should be counted.
    :return The number of documents in the collection.
    """
    return collection.count()


def save(database, document, manipulate=False):
    """Save one document into the database.

    :param database: The database where to save.
    :param documents: The document to save, can be a list or a single document:
        the type of each document must be: BaseDocument or a subclass.
    :type list, BaseDocument
    :param manipulate: If the passed documents have to be manipulated by
    mongodb. Default to False.
    :type manipulate: bool
    :return A tuple: first element is the operation code (201 if the save has
    success, 500 in case of an error), second element is the mongodb created
    `_id` value if manipulate is True, or None.
    """
    ret_value = 201
    doc_id = None

    if isinstance(document, mbase.BaseDocument):
        to_save = document.to_dict()
    else:
        utils.LOG.warn(
            "Cannot save document, it is not of type BaseDocument, got %s",
            type(document))

    try:
        doc_id = database[document.collection].save(
            to_save, manipulate=manipulate)
        utils.LOG.info(
            "Document '%s' saved (%s)", document.name, document.collection)
    except pymongo.errors.OperationFailure, ex:
        utils.LOG.error(
            "Error saving the following document: %s (%s)",
            document.name, document.collection
        )
        utils.LOG.exception(ex)
        ret_value = 500

    return ret_value, doc_id


def save_all(database, documents, manipulate=False, fail_on_err=False):
    """Save a list of documents.

    :param database: The database where to save.
    :param documents: The list of `BaseDocument` documents.
    :type documents: list
    :param manipulate: If the database has to create an _id attribute for each
    document. Default False.
    :type manipulate: bool
    :param fail_on_err: If in case of an error the save operation should stop
    immediatly. Default False.
    :type fail_on_err: bool
    :return A tuple: first element is the operation code (201 if the save has
    success, 500 in case of an error), second element is the list of the
    mongodb created `_id` values for each document if manipulate is True, or a
    list of None values.
    """
    ret_value = 201
    doc_id = []

    if not isinstance(documents, types.ListType):
        documents = [documents]

    for document in documents:
        if isinstance(document, mbase.BaseDocument):
            ret_value, save_id = save(
                database, document, manipulate=manipulate)
            doc_id.append(save_id)

            if fail_on_err and ret_value == 500:
                break
        else:
            utils.LOG.error(
                "Cannot save document, it is not of type BaseDocument, got %s",
                type(document))
            doc_id.append(None)

            if fail_on_err:
                ret_value = 500
                break

    return ret_value, doc_id


def update(collection, spec, document, operation="$set"):
    """Update a document with the provided values.

    The operation is performed on the collection based on the `spec` provided.
    `spec` can specify any document fields. `document` is a dict with the
    key-value to update.

    The default operation performed is `$set`.

    :param spec: The fields that will be matched in the document to update.
    :type dict
    :param document: The key-value to update.
    :type dict
    :param operation: The operation to perform. By default is `$set`.
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
    except pymongo.errors.OperationFailure, ex:
        utils.LOG.error(
            "Error updating the following document: %s", str(document))
        utils.LOG.exception(str(ex))
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
    except pymongo.errors.OperationFailure, ex:
        utils.LOG.error(
            "Error removing the following document: %s", str(spec_or_id))
        utils.LOG.exception(str(ex))
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
        if val[0] != "$":
            val = "$" + val
        return val

    # Where the aggregate actions and values will be stored.
    pipeline = []

    if match is not None:
        pipeline.append({
            "$match": match
        })

    # XXX: For strange reasons, sort needs to happen before, and also
    # after grouping, or the resulsts are completely random
    if sort is not None:
        pipeline.append({
            "$sort": {
                k: v for k, v in sort
            }
        })

    group_dict = {
        "$group": {
            "_id": _starts_with_dollar(unique)
        }
    }

    if fields is not None:
        fields = [
            (k, v) for k, v in [
                (key, val)
                for key in fields
                for val in [{"$first": _starts_with_dollar(key)}]
            ]
        ]
    else:
        fields = [("result", {"$first": "$$CURRENT"})]

    group_dict["$group"].update(fields)
    pipeline.append(group_dict)

    # XXX: For strange reasons, sort needs to happen before, and also
    # after grouping, or the resulsts are completely random
    if sort is not None:
        pipeline.append({
            "$sort": {
                k: v for k, v in sort
            }
        })

    # Make sure we return the exact number of elements after grouping them.
    if all([limit is not None, limit > 0]):
        pipeline.append({
            "$limit": limit
        })

    utils.LOG.debug(pipeline)

    result = collection.aggregate(pipeline)

    if result and isinstance(result, types.DictionaryType):
        element = result.get("result", None)

        if all([
                element,
                isinstance(element, types.ListType), len(element) > 0]):
            r_element = element[0]

            if r_element.get("result", None):
                result = [
                    k["result"] for k in [v for v in element]
                ]
            else:
                result = [k for k in element]
        else:
            result = []

    return result
