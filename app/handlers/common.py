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

"""Set of common functions for all handlers."""

import types

from bson import tz_util
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from pymongo import (
    ASCENDING,
    DESCENDING,
)

from models import (
    ADMIN_KEY,
    AGGREGATE_KEY,
    ARCHITECTURE_KEY,
    BOARD_KEY,
    BOOT_COLLECTION,
    COLLECTION_KEY,
    CREATED_KEY,
    DATE_RANGE_KEY,
    DEFCONFIG_COLLECTION,
    DEFCONFIG_KEY,
    DELETE_KEY,
    DOCUMENT_ID_KEY,
    EMAIL_KEY,
    ERRORS_KEY,
    EXPIRED_KEY,
    EXPIRES_KEY,
    FIELD_KEY,
    GET_KEY,
    IP_ADDRESS_KEY,
    IP_RESTRICTED,
    JOB_COLLECTION,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    LIMIT_KEY,
    METHOD_KEY,
    NOT_FIELD_KEY,
    OP_ID_KEY,
    POST_KEY,
    PRIVATE_KEY,
    PROPERTIES_KEY,
    QUERY_KEY,
    SKIP_KEY,
    SORT_KEY,
    SORT_ORDER_KEY,
    STATUS_KEY,
    SUPERUSER_KEY,
    TIME_KEY,
    TOKEN_KEY,
    USERNAME_KEY,
    WARNINGS_KEY,
)
from utils import get_log

# Default value to calculate a date range in case the provided value is
# out of range.
DEFAULT_DATE_RANGE = 15

LOG = get_log()

# All the available collections as key-value. The key is the same used for the
# URL configuration.
COLLECTIONS = {
    'boot': BOOT_COLLECTION,
    'defconfig': DEFCONFIG_COLLECTION,
    'job': JOB_COLLECTION,
}

# Handlers valid keys.
BOOT_VALID_KEYS = {
    'POST': [JOB_KEY, KERNEL_KEY],
    'GET': [
        CREATED_KEY, WARNINGS_KEY, JOB_ID_KEY, BOARD_KEY,
        JOB_KEY, KERNEL_KEY, DEFCONFIG_KEY, TIME_KEY, STATUS_KEY,
    ],
    'DELETE': [
        JOB_KEY, KERNEL_KEY, DEFCONFIG_KEY, BOARD_KEY, JOB_ID_KEY
    ]
}

COUNT_VALID_KEYS = {
    'GET': [
        ARCHITECTURE_KEY,
        BOARD_KEY,
        CREATED_KEY,
        DEFCONFIG_KEY,
        ERRORS_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        PRIVATE_KEY,
        STATUS_KEY,
        TIME_KEY,
        WARNINGS_KEY,
    ],
}

DEFCONFIG_VALID_KEYS = {
    'GET': [
        DEFCONFIG_KEY, WARNINGS_KEY, ERRORS_KEY, ARCHITECTURE_KEY,
        JOB_KEY, KERNEL_KEY, STATUS_KEY, JOB_ID_KEY, CREATED_KEY,
    ],
}

TOKEN_VALID_KEYS = {
    'POST': [
        ADMIN_KEY,
        DELETE_KEY,
        EMAIL_KEY,
        EXPIRES_KEY,
        GET_KEY,
        IP_ADDRESS_KEY,
        IP_RESTRICTED,
        POST_KEY,
        SUPERUSER_KEY,
        USERNAME_KEY,
    ],
    'GET': [
        CREATED_KEY,
        EMAIL_KEY,
        EXPIRED_KEY,
        EXPIRES_KEY,
        IP_ADDRESS_KEY,
        PROPERTIES_KEY,
        TOKEN_KEY,
        USERNAME_KEY,
    ],
}

SUBSCRIPTION_VALID_KEYS = {
    'GET': [JOB_KEY],
    'POST': [JOB_KEY, EMAIL_KEY],
    'DELETE': [EMAIL_KEY],
}

JOB_VALID_KEYS = {
    'POST': [JOB_KEY, KERNEL_KEY],
    'GET': [
        JOB_KEY, KERNEL_KEY, STATUS_KEY, PRIVATE_KEY, CREATED_KEY,
    ],
}

BATCH_VALID_KEYS = {
    "POST": [
        METHOD_KEY, COLLECTION_KEY, QUERY_KEY, OP_ID_KEY,
        DOCUMENT_ID_KEY
    ]
}


def get_all_query_values(query_args_func, valid_keys):
    """Handy function to get all query args in a batch.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: A list containing the valid keys that should be
    retrieved.
    :type valid_keys: list
    """
    spec = get_query_spec(query_args_func, valid_keys)
    spec = get_and_add_date_range(spec, query_args_func)

    sort = get_query_sort(query_args_func)
    fields = get_query_fields(query_args_func)
    skip, limit = get_skip_and_limit(query_args_func)
    unique = get_aggregate_value(query_args_func)

    return (spec, sort, fields, skip, limit, unique)


def get_aggregate_value(query_args_func):
    """Get teh value of the aggregate key.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :return The aggregate value as string.
    """
    aggregate = query_args_func(AGGREGATE_KEY)
    if all([aggregate and isinstance(aggregate, types.ListType)]):
        aggregate = aggregate[-1]
    else:
        aggregate = None
    return aggregate


def get_query_spec(query_args_func, valid_keys):
    """Get values from the query string to build a `spec` data structure.

    A `spec` data structure is a dictionary whose keys are the keys
    accepted by this handler method.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: A list containing the valid keys that should be
    retrieved.
    :type valid_keys: list
    :return A `spec` data structure (dictionary).
    """
    def _get_spec_values():
        """Get the values for the spec data structure.

        Internally used only, with some logic to differentiate between single
        and multiple values. Makes sure also that the list of values if valid,
        meaning that we do not have None or empty values.

        :return A tuple with the key and its value.
        """
        for key in valid_keys:
            val = query_args_func(key) or []
            if val:
                # Go through the values and make sure we have valid ones.
                val = [v for v in val if v]
                len_val = len(val)

                if len_val == 1:
                    val = val[0]
                elif len_val > 1:
                    # More than one value, make sure we look for all of them.
                    val = {'$in': val}

            yield key, val

    spec = {}
    if all([valid_keys and isinstance(valid_keys, types.ListType)]):
        spec = {
            k: v for k, v in [
                (key, val)
                for key, val in _get_spec_values()
                if val
            ]
        }

    return spec


def get_and_add_date_range(spec, query_args_func):
    """Retrieve the `date_range` query from the request.

    Add the retrieved `date_range` value into the provided `spec` data
    structure.

    :param spec: The dictionary where to store the key-value.
    :type spec: dictionary
    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return The passed `spec` updated.
    """
    date_range = query_args_func(DATE_RANGE_KEY)
    if date_range:
        # Today needs to be set at the end of the day!
        today = datetime.combine(
            date.today(), time(23, 59, 59, tzinfo=tz_util.utc)
        )
        previous = calculate_date_range(date_range)

        spec[CREATED_KEY] = {'$gte': previous, '$lt': today}
    return spec


def calculate_date_range(date_range):
    """Calculate the new date subtracting the passed number of days.

    It removes the passed days from today date, calculated at midnight
    UTC.

    :param date_range: The number of days to remove from today.
    :type date_range int, long, str
    :return A new `datetime.date` object that is the result of the
    subtraction of `datetime.date.today()` and
    `datetime.timedelta(days=date_range)`.
    """
    if isinstance(date_range, types.ListType):
        date_range = date_range[-1]

    if isinstance(date_range, types.StringTypes):
        date_range = int(date_range)

    date_range = abs(date_range)
    if date_range > timedelta.max.days:
        date_range = DEFAULT_DATE_RANGE

    # Calcuate with midnight in mind though, so we get the starting of
    # the day for the previous date.
    today = datetime.combine(
        date.today(), time(tzinfo=tz_util.utc)
    )
    delta = timedelta(days=date_range)

    return today - delta


def get_query_fields(query_args_func):
    """Get values from the query string to build a `fields` data structure.

    A `field` data structure can be either a list or a dictionary.

    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return A `fields` data structure (list or dictionary).
    """
    fields = None
    y_fields, n_fields = map(query_args_func, [FIELD_KEY, NOT_FIELD_KEY])

    if y_fields and not n_fields:
        fields = list(set(y_fields))
    elif n_fields:
        fields = dict.fromkeys(list(set(y_fields)), True)
        fields.update(dict.fromkeys(list(set(n_fields)), False))

    return fields


def get_query_sort(query_args_func):
    """Get values from the query string to build a `sort` data structure.

    A `sort` data structure is a list of tuples in a `key-value` fashion.
    The keys are the values passed as the `sort` argument on the query,
    they values are based on the `sort_order` argument and defaults to the
    descending order.

    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return A `sort` data structure, or None.
    """
    sort = None
    sort_fields, sort_order = map(query_args_func, [SORT_KEY, SORT_ORDER_KEY])

    if sort_fields:
        if all([sort_order, isinstance(sort_order, types.ListType)]):
            sort_order = int(sort_order[-1])
        else:
            sort_order = DESCENDING

        # Wrong number for sort order? Force descending.
        if all([sort_order != ASCENDING, sort_order != DESCENDING]):
            LOG.warn(
                "Wrong sort order used (%d), default to %d",
                sort_order, DESCENDING
            )
            sort_order = DESCENDING

        sort = [
            (field, sort_order)
            for field in sort_fields
        ]

    return sort


def get_skip_and_limit(query_args_func):
    """Retrieve the `skip` and `limit` query arguments.

    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return A tuple with the `skip` and `limit` arguments.
    """
    skip, limit = map(query_args_func, [SKIP_KEY, LIMIT_KEY])

    if all([skip, isinstance(skip, types.ListType)]):
        skip = int(skip[-1])
    else:
        skip = 0

    if all([limit, isinstance(limit, types.ListType)]):
        limit = int(limit[-1])
    else:
        limit = 0

    return skip, limit
