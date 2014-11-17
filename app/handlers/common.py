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

import pymongo
import types

from bson import (
    objectid,
    tz_util,
)
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)

import models
import models.token as mtoken
import utils

# Default value to calculate a date range in case the provided value is
# out of range.
DEFAULT_DATE_RANGE = 5

# All the available collections as key-value. The key is the same used for the
# URL configuration.
COLLECTIONS = {
    'boot': models.BOOT_COLLECTION,
    'defconfig': models.DEFCONFIG_COLLECTION,
    'job': models.JOB_COLLECTION,
}

# Handlers valid keys.
BOOT_VALID_KEYS = {
    'POST': {
        models.MANDATORY_KEYS: [
            models.BOARD_KEY,
            models.DEFCONFIG_KEY,
            models.JOB_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
        ],
        models.ACCEPTED_KEYS: [
            models.ARCHITECTURE_KEY,
            models.BOARD_KEY,
            models.BOOT_LOG_KEY,
            models.BOOT_RESULT_DESC_KEY,
            models.BOOT_RESULT_KEY,
            models.BOOT_RETRIES_KEY,
            models.BOOT_TIME_KEY,
            models.BOOT_WARNINGS_KEY,
            models.DTB_ADDR_KEY,
            models.DTB_KEY,
            models.EMAIL_KEY,
            models.ENDIANNESS_KEY,
            models.FASTBOOT_KEY,
            models.GIT_COMMIT_KEY,
            models.GIT_DESCRIBE_KEY,
            models.ID_KEY,
            models.INITRD_ADDR_KEY,
            models.JOB_KEY,
            models.KERNEL_IMAGE_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
            models.NAME_KEY,
            models.STATUS_KEY,
            models.VERSION_KEY,
        ]
    },
    'GET': [
        models.BOARD_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_KEY,
        models.ENDIANNESS_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.LAB_NAME_KEY,
        models.NAME_KEY,
        models.STATUS_KEY,
        models.WARNINGS_KEY,
    ],
    'DELETE': [
        models.BOARD_KEY,
        models.DEFCONFIG_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
    ]
}

COUNT_VALID_KEYS = {
    'GET': [
        models.ARCHITECTURE_KEY,
        models.BOARD_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_KEY,
        models.ERRORS_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_DESCRIBE_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
        models.PRIVATE_KEY,
        models.STATUS_KEY,
        models.TIME_KEY,
        models.WARNINGS_KEY,
    ],
}

DEFCONFIG_VALID_KEYS = {
    'GET': [
        models.ARCHITECTURE_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_KEY,
        models.ERRORS_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_COMMIT_KEY,
        models.GIT_DESCRIBE_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
        models.STATUS_KEY,
        models.WARNINGS_KEY,
    ],
}

TOKEN_VALID_KEYS = {
    'POST': [
        models.ADMIN_KEY,
        models.DELETE_KEY,
        models.EMAIL_KEY,
        models.EXPIRES_KEY,
        models.GET_KEY,
        models.IP_ADDRESS_KEY,
        models.IP_RESTRICTED,
        models.NAME_KEY,
        models.POST_KEY,
        models.SUPERUSER_KEY,
        models.USERNAME_KEY,
    ],
    'GET': [
        models.CREATED_KEY,
        models.EMAIL_KEY,
        models.EXPIRED_KEY,
        models.EXPIRES_KEY,
        models.ID_KEY,
        models.IP_ADDRESS_KEY,
        models.NAME_KEY,
        models.PROPERTIES_KEY,
        models.TOKEN_KEY,
        models.USERNAME_KEY,
    ],
}

SUBSCRIPTION_VALID_KEYS = {
    'GET': [
        models.JOB_KEY
    ],
    'POST': [
        models.EMAIL_KEY,
        models.JOB_KEY,
    ],
    'DELETE': [
        models.EMAIL_KEY
    ],
}

JOB_VALID_KEYS = {
    'POST': [
        models.JOB_KEY,
        models.KERNEL_KEY
    ],
    'GET': [
        models.CREATED_KEY,
        models.ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
        models.PRIVATE_KEY,
        models.STATUS_KEY,
    ],
}

BATCH_VALID_KEYS = {
    "POST": [
        models.COLLECTION_KEY,
        models.DOCUMENT_ID_KEY,
        models.METHOD_KEY,
        models.OP_ID_KEY,
        models.QUERY_KEY,
    ]
}

LAB_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.CONTACT_KEY,
            models.NAME_KEY,
        ],
        models.ACCEPTED_KEYS: [
            models.ADDRESS_KEY,
            models.CONTACT_KEY,
            models.NAME_KEY,
            models.PRIVATE_KEY,
            models.TOKEN_KEY,
        ]
    },
    "GET": [
        models.ADDRESS_KEY,
        models.CONTACT_KEY,
        models.CREATED_KEY,
        models.ID_KEY,
        models.NAME_KEY,
        models.PRIVATE_KEY,
        models.TOKEN_KEY,
        models.UPDATED_KEY,
    ],
    "DELETE": [
        models.ADDRESS_KEY,
        models.CONTACT_KEY,
        models.ID_KEY,
        models.NAME_KEY,
        models.TOKEN_KEY,
    ]
}

ID_KEYS = [
    models.BOOT_ID_KEY,
    models.DEFCONFIG_ID_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.LAB_ID_KEY,
]

MASTER_KEY = 'master_key'
API_TOKEN_HEADER = 'Authorization'
ACCEPTED_CONTENT_TYPE = 'application/json'
DEFAULT_RESPONSE_TYPE = 'application/json; charset=UTF-8'
NOT_VALID_TOKEN = "Operation not permitted: check the token permissions"


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

    get_and_add_date_range(spec, query_args_func)
    update_id_fields(spec)

    sort = get_query_sort(query_args_func)
    fields = get_query_fields(query_args_func)
    skip, limit = get_skip_and_limit(query_args_func)
    unique = get_aggregate_value(query_args_func)

    return (spec, sort, fields, skip, limit, unique)


def update_id_fields(spec):
    """Make sure ID fields are treated correctly.

    If we search for an ID field, either _id or like job_id, that references
    a real _id in mongodb, we need to make sure they are treated as such.
    mongodb stores them as ObjectId elements.

    :param spec: The spec data structure with the parameters to check.
    """
    if spec:
        common_keys = list(set(ID_KEYS) & set(spec.viewkeys()))
        for key in common_keys:
            spec[key] = objectid.ObjectId(spec[key])


def get_aggregate_value(query_args_func):
    """Get teh value of the aggregate key.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :return The aggregate value as string.
    """
    aggregate = query_args_func(models.AGGREGATE_KEY)
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
    date_range = query_args_func(models.DATE_RANGE_KEY)
    if date_range:
        # Today needs to be set at the end of the day!
        today = datetime.combine(
            date.today(), time(23, 59, 59, tzinfo=tz_util.utc)
        )
        previous = calculate_date_range(date_range)

        spec[models.CREATED_KEY] = {'$gte': previous, '$lt': today}
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
        try:
            date_range = int(date_range)
        except ValueError:
            utils.LOG.error(
                "Wrong value passed to date_range: %s", date_range
            )
            date_range = DEFAULT_DATE_RANGE

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

    A `fields` data structure can be either a list or a dictionary.

    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return A `fields` data structure (list or dictionary).
    """
    fields = None
    y_fields, n_fields = map(
        query_args_func, [models.FIELD_KEY, models.NOT_FIELD_KEY]
    )

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
    sort_fields, sort_order = map(
        query_args_func, [models.SORT_KEY, models.SORT_ORDER_KEY]
    )

    if sort_fields:
        if all([sort_order, isinstance(sort_order, types.ListType)]):
            sort_order = int(sort_order[-1])
        else:
            sort_order = pymongo.DESCENDING

        # Wrong number for sort order? Force descending.
        if all([sort_order != pymongo.ASCENDING,
                sort_order != pymongo.DESCENDING]):
            utils.LOG.warn(
                "Wrong sort order used (%d), default to %d",
                sort_order, pymongo.DESCENDING
            )
            sort_order = pymongo.DESCENDING

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
    skip, limit = map(query_args_func, [models.SKIP_KEY, models.LIMIT_KEY])

    if all([skip, isinstance(skip, types.ListType)]):
        skip = int(skip[-1])
    else:
        skip = 0

    if all([limit, isinstance(limit, types.ListType)]):
        limit = int(limit[-1])
    else:
        limit = 0

    return skip, limit


def valid_token_general(token, method):
    """Make sure the token can be used for an HTTP method.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if method == "GET" and token.is_get_token:
        valid_token = True
    elif method == "POST" and token.is_post_token:
        valid_token = True
    elif method == "DELETE" and token.is_delete_token:
        valid_token = True

    return valid_token


def valid_token_th(token, method):
    """Make sure a token is a valid token for the `TokenHandler`.

    A valid `TokenHandler` token is an admin token, or a superuser token
    for GET operations.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if token.is_admin:
        valid_token = True
    elif token.is_superuser and method == "GET":
        valid_token = True

    return valid_token


def validate_token(token_obj, method, remote_ip, validate_func):
    """Make sure the passed token is valid.

    :param token_obj: The JSON object from the db that contains the token.
    :param method: The HTTP verb this token is being validated for.
    :param remote_ip: The remote IP address sending the token.
    :param validate_func: Function called to validate the token, must accept
        a Token object, the method string and kwargs.
    :return True or False.
    """
    valid_token = True

    if token_obj:
        token = mtoken.Token.from_json(token_obj)

        if not isinstance(token, mtoken.Token):
            utils.LOG.error("Retrieved token is not a Token object")
            valid_token = False
        else:
            valid_token &= validate_func(token, method)

            if token.is_ip_restricted and \
                    not _valid_token_ip(token, remote_ip):
                valid_token = False
    else:
        valid_token = False

    return valid_token


def _valid_token_ip(token, remote_ip):
    """Make sure the token comes from the designated IP addresses.

    :param token: The Token object to validate.
    :param remote_ip: The remote IP address sending the token.
    :return True or False.
    """
    valid_token = False

    if remote_ip:
        remote_ip = mtoken.convert_ip_address(remote_ip)

        if remote_ip in token.ip_address:
            valid_token = True
        else:
            utils.LOG.warn(
                "IP restricted token from wrong IP address: %s",
                remote_ip
            )
    else:
        utils.LOG.info("No remote IP address provided, cannot validate token")

    return valid_token
