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


def find_one_async(collection, doc_id, callback):
    """Search a single document by its id.

    Accepts an extra callback function that will be called with the results.

    :param collection: The collection where to search.
    :param doc_id: The '_id' of the document to find.
    :param callback: Function to call with the results.
    :return None or the search result.
    """
    result = find_one(collection, doc_id)
    callback(result)


def find_one(collection, values, field="_id"):
    """Search a single document by its id.

    :param collection: The collection where to search.
    :param values: The values to search. Can be a list of multiple values.
    :param field: The field where the value should be searched.
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


def find_one_where(collection, field, values):
    result = collection.find_one(
        {
            field: {"$in": values}
        }
    )

    return result


def find_async(collection, limit, skip, callback):
    callback(find(collection, limit, skip))


def find(collection, limit, skip):
    return collection.find(limit=limit, skip=skip)
