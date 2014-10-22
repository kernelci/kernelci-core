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

from types import (
    ListType,
    StringTypes,
)

from models import (
    BOOT_COLLECTION,
    COLLECTION_KEY,
    COUNT_COLLECTION,
    DEFCONFIG_COLLECTION,
    DOCUMENT_ID_KEY,
    JOB_COLLECTION,
    METHOD_KEY,
    OP_ID_KEY,
    QUERY_KEY,
)
from utils.batch.batch_op import (
    BatchBootOperation,
    BatchCountOperation,
    BatchDefconfigOperation,
    BatchJobOperation,
    BatchOperation,
)
from utils.db import get_db_connection


def create_batch_operation(json_obj, db_options):
    """Create a `BatchOperation` object from a JSON object.

    No validity checks are performed on the JSON object, it must be a valid
    batch operation JSON structure.

    :param json_obj: The JSON object with all the necessary paramters.
    :type json_obj: dict
    :param db_options: The mongodb configuration parameters.
    :type db_options: dict
    :return A `BatchOperation` object, or None if the `BatchOperation` cannot
    be constructed.
    """
    batch_op = None

    if json_obj:
        get_func = json_obj.get
        collection = get_func(COLLECTION_KEY, None)

        if collection:
            database = get_db_connection(db_options)
            operation_id = get_func(OP_ID_KEY, None)

            if collection == COUNT_COLLECTION:
                batch_op = BatchCountOperation(
                    collection, database, operation_id=operation_id
                )
            elif collection == BOOT_COLLECTION:
                batch_op = BatchBootOperation(
                    collection, database, operation_id=operation_id
                )
            elif collection == JOB_COLLECTION:
                batch_op = BatchJobOperation(
                    collection, database, operation_id=operation_id
                )
            elif collection == DEFCONFIG_COLLECTION:
                batch_op = BatchDefconfigOperation(
                    collection, database, operation_id=operation_id)
            else:
                batch_op = BatchOperation(
                    collection, database, operation_id=operation_id)

            batch_op.query_args = get_batch_query_args(
                get_func(QUERY_KEY, None)
            )
            batch_op.document_id = get_func(DOCUMENT_ID_KEY, None)
            batch_op.query_args_func = batch_op.query_args.get
            batch_op.method = get_func(METHOD_KEY, None)

    return batch_op


def execute_batch_operation(json_obj, db_options):
    """Create and execute the batch op as defined in the JSON object.

    :param json_obj: The JSON object that will be used to create the batch
    operation.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return The result of the operation execution, or None.
    """
    batch_op = create_batch_operation(json_obj, db_options)

    result = None
    if batch_op:
        result = batch_op.run()

    return result


def get_batch_query_args(query):
    """From a query string, retrieve the key-value pairs.

    The query string has to be built as a normal HTTP query: it can either
    start with a question mark or not, key and values must be separated
    by an equal sign (=), and multiple key-value pairs must be separated
    by an ampersand (&):

        [?]key=value[&key=value&key=value...]

    The values are then retrieved and stored in a set to avoid duplicates.

    :param query: The query string to analyze.
    :type query: string
    :return A dictionary with keys the keys from the query, and values the
    values stored in a list.
    """
    args = {}

    if all([query, isinstance(query, StringTypes)]):
        if query.startswith("?"):
            query = query[1:]

        query = query.split("&")
        if isinstance(query, ListType):
            for arg in query:
                arg = arg.split("=")
                # Can't have query with just one element, they have to be
                # key=value.
                if len(arg) > 1:
                    if args.get(arg[0], None):
                        args[arg[0]].append(arg[1])
                    else:
                        args[arg[0]] = list([arg[1]])
                    args[arg[0]] = list(set(args[arg[0]]))

    return args
