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
    AGGREGATE_KEY,
    CREATED_KEY,
    DATE_RANGE_KEY,
    FIELD_KEY,
    LIMIT_KEY,
    NOT_FIELD_KEY,
    SKIP_KEY,
    SORT_KEY,
    SORT_ORDER_KEY,
)
from utils import get_log

# Default value to calculate a date range in case the provided value is
# out of range.
DEFAULT_DATE_RANGE = 15

LOG = get_log()


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
    spec = {}
    if all([valid_keys and isinstance(valid_keys, types.ListType)]):
        spec = {
            k: v for k, v in [
                (key, val)
                for key in valid_keys
                for val in query_args_func(key)
                if val is not None
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
        if isinstance(date_range, types.ListType):
            date_range = date_range[-1]
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

    y_fields = query_args_func(FIELD_KEY)
    n_fields = query_args_func(NOT_FIELD_KEY)

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
    :return A `sort` data structure.
    """
    sort = None
    sort_fields = query_args_func(SORT_KEY)
    sort_order = query_args_func(SORT_ORDER_KEY)

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
    skip = 0
    limit = 0

    skip = query_args_func(SKIP_KEY)
    if all([skip, isinstance(skip, types.ListType)]):
        skip = int(skip[-1])
    else:
        skip = 0

    limit = query_args_func(LIMIT_KEY)
    if limit and isinstance(limit, types.ListType):
        limit = int(limit[-1])
    else:
        limit = 0

    return skip, limit
