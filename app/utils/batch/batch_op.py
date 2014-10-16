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

"""Batch operation classes."""

from bson.json_util import dumps

from handlers.common import (
    BOOT_VALID_KEYS,
    COUNT_VALID_KEYS,
    DEFCONFIG_VALID_KEYS,
    JOB_VALID_KEYS,
    get_all_query_values,
    get_query_fields,
)
from handlers.count import (
    count_all_collections,
    count_one_collection,
)
from models import (
    COUNT_KEY,
    OP_ID_KEY,
    RESULT_KEY,
)
from utils import get_log
from utils.db import (
    aggregate,
    find_and_count,
    find_one,
)

LOG = get_log()


class BatchOperation(object):
    """The base batch operation that can be performed.

    Specialized operations, for count or other collections, should be created
    starting from this class.
    """

    def __init__(self, collection, database, operation_id=None):
        """Create a new `BatchOperation`.

        :param collection: The db collection where to perform the operation.
        :type collection: string
        :param database: The mongodb database connection.
        :type database: `pymongo.Database`
        :param operation_id: Optional name for this operation.
        :type operation_id: string
        """
        self._database = database
        self._operation_id = operation_id
        self._collection = collection
        self._operation = None
        self.args = []
        self.kwargs = {}
        self.query_args = {}
        self.valid_keys = None
        self.document_id = None
        self.method = None
        self.query_args_func = None

    @property
    def operation(self):
        """Get the (real) operation associated with this batch op.

        It should be a function that will be called when invoking `run()` and
        it should accept `*args` and `**kwargs` parameters.
        """
        return self._operation

    @operation.setter
    def operation(self, value):
        """Set the operation to be performed when invoking `run()`.

        :param value: The operation to set.
        :type value: function
        """
        self._operation = value

    @property
    def operation_id(self):
        """Get the ID of this batch operation.

        The operation ID is a name associated with this batch operation. If
        provided it will be returned in the response.

        Useful to differentiate between multiple operations in a single batch.
        """
        return self._operation_id

    @operation_id.setter
    def operation_id(self, value):
        """Set the operation ID value.

        :param value: The operation ID to set.
        :param value: string
        """
        self._operation_id = value

    def prepare_operation(self):
        """Prepare the operation that needs to be performed.

        This method is automatically called when invoking `run()` to make sure
        all necessary parameters are set up correctly.

        Subclasses should not override this method, but instead override the
        private ones specialized for each HTTP verbs.
        """
        if self.method == "GET":
            self._prepare_get_operation()
        elif self.method == "DELETE":
            self._prepare_delete_operation()
        elif self.method == "POST":
            self._prepare_post_operation()

    def _prepare_get_operation(self):
        """Prepare the necessary parameters for a GET operation."""
        if self.document_id:
            # Get only one document.
            self.operation = find_one
            self.args = [
                self._database[self._collection],
                self.document_id,
            ]
            self.kwargs = {
                'fields': get_query_fields(self.query_args_func)
            }
        else:
            # Get the spec and perform the query, can perform and aggregation
            # as well.
            spec, sort, fields, skip, limit, unique = get_all_query_values(
                self.query_args_func, self.valid_keys.get(self.method)
            )

            if unique:
                # Perform an aggregate
                self.operation = aggregate
                self.args = [
                    self._database[self._collection],
                    unique
                ]
                self.kwargs = {
                    'sort': sort,
                    'fields': fields,
                    'match': spec,
                    'limit': limit
                }
            else:
                self.operation = find_and_count
                self.args = [
                    self._database[self._collection],
                    limit,
                    skip,
                ]
                self.kwargs = {
                    'spec': spec,
                    'fields': fields,
                    'sort': sort
                }

    def _prepare_post_operation(self):
        """Prepare the necessary parameters for a POST operation."""
        raise NotImplementedError

    def _prepare_delete_operation(self):
        """Prepare the necessary parameters for a DELETE operation."""
        raise NotImplementedError

    def _prepare_response(self, result):
        """Prepare the response to be returned.

        :param result: The result obtained after invoking the `operation`.
        :return A dictionary
        """
        response = {}
        if self.operation_id:
            response[OP_ID_KEY] = self.operation_id

        # find_and_count returns 2 results: the mongodb cursor and the
        # results count.
        if isinstance(result, tuple):
            # Doing like this otherwise the result returned will be a string
            # and not a real JSON object (since we have to serialize it here).
            count = result[1]
            res = []

            if count > 0:
                res = [r for r in result[0]]

            response[RESULT_KEY] = [
                dumps(
                    {
                        RESULT_KEY: res,
                        COUNT_KEY: count
                    }
                )
            ]
        else:
            response[RESULT_KEY] = result

        return response

    def run(self):
        """Prepare and run this operation.

        This method will invoke the `operation` attribute as a function, passing
        the defined `args` and `kwargs` parameters.
        """
        self.prepare_operation()

        result = []
        if self.operation:
            result = self.operation(*self.args, **self.kwargs)
        return self._prepare_response(result)


class BatchBootOperation(BatchOperation):
    """A batch operation for the `boot` collection."""

    def __init__(self, collection, database, operation_id=None):
        super(BatchBootOperation, self).__init__(
            collection, database, operation_id
        )
        self.valid_keys = BOOT_VALID_KEYS


class BatchJobOperation(BatchOperation):
    """A batch operation for the `job` collection."""

    def __init__(self, collection, database, operation_id=None):
        super(BatchJobOperation, self).__init__(
            collection, database, operation_id
        )
        self.valid_keys = JOB_VALID_KEYS


class BatchDefconfigOperation(BatchOperation):
    """A batch operation for the `job` collection."""

    def __init__(self, collection, database, operation_id=None):
        super(BatchDefconfigOperation, self).__init__(
            collection, database, operation_id
        )
        self.valid_keys = DEFCONFIG_VALID_KEYS


class BatchCountOperation(BatchOperation):
    """A batch operation for the `count` collection."""

    def __init__(self, collection, database, operation_id=None):
        super(BatchCountOperation, self).__init__(
            collection, database, operation_id
        )
        self.valid_keys = COUNT_VALID_KEYS

    def _prepare_get_operation(self):
        if self.document_id:
            self.operation = count_one_collection
            self.args = [
                self._database[self.document_id],
                self.document_id,
                self.query_args_func,
                self.valid_keys.get(self.method)
            ]
        else:
            self.operation = count_all_collections
            self.args = [
                self._database,
                self.query_args_func,
                self.valid_keys.get(self.method)
            ]
