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

"""Common functions for batch operations."""

import types

import models
import utils.batch.batch_op as batchop


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

    if all([query, isinstance(query, types.StringTypes)]):
        if query.startswith("?"):
            query = query[1:]

        query = query.split("&")
        if isinstance(query, types.ListType):
            for arg in query:
                arg = arg.split("=")
                # Can't have query with just one element, they have to be
                # key=value.
                if len(arg) > 1:
                    try:
                        args[arg[0]].append(arg[1])
                        args[arg[0]] = list(set(args[arg[0]]))
                    except KeyError:
                        args[arg[0]] = []
                        args[arg[0]].append(arg[1])

    return args


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
    get_func = None

    def _complete_batch_op():
        batch_op.db_options = db_options
        batch_op.query_args = get_batch_query_args(
            get_func(models.QUERY_KEY, None))

        for key, val in json_obj.iteritems():
            setattr(batch_op, key, val)

    if json_obj:
        get_func = json_obj.get
        resource = get_func(models.RESOURCE_KEY, None)
        distinct = get_func(models.DISTINCT_KEY, None)
        document = get_func(models.DOCUMENT_KEY, None)

        if resource in models.COLLECTIONS:
            # Check first if we have a count-distinct or distinct operation
            # to perform.
            if all([distinct, document]):
                batch_op = batchop.BatchCountDistinctOperation()
            elif all([distinct, not document]):
                batch_op = batchop.BatchDistinctOperation()
            # Then in case proceed with the normal operations.
            elif resource:
                if resource == models.COUNT_COLLECTION:
                    batch_op = batchop.BatchCountOperation()
                elif resource == models.BOOT_COLLECTION:
                    batch_op = batchop.BatchBootOperation()
                elif resource == models.JOB_COLLECTION:
                    batch_op = batchop.BatchJobOperation()
                elif resource == models.BUILD_COLLECTION:
                    batch_op = batchop.BatchBuildOperation()
                elif resource == models.TEST_CASE_COLLECTION:
                    batch_op = batchop.BatchTestCaseOperation()
                elif resource == models.TEST_SUITE_COLLECTION:
                    batch_op = batchop.BatchTestSuiteOperation()

            _complete_batch_op()

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
