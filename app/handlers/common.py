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

import bson
import datetime
import pymongo
import types

import models
import models.token as mtoken
import utils

# Default value to calculate a date range in case the provided value is
# out of range.
DEFAULT_DATE_RANGE = 5

# All the available collections as key-value. The key is the same used for the
# URL configuration.
COLLECTIONS = {
    "boot": models.BOOT_COLLECTION,
    "defconfig": models.DEFCONFIG_COLLECTION,
    "job": models.JOB_COLLECTION,
    "test_suite": models.TEST_SUITE_COLLECTION,
    "test_set": models.TEST_SET_COLLECTION,
    "test_case": models.TEST_CASE_COLLECTION
}

# Some key values must be treated in a different way, not as string.
KEY_TYPES = {
    models.RETRIES_KEY: "int",
    models.WARNINGS_KEY: "int"
}

# Handlers valid keys.
BOOT_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.ARCHITECTURE_KEY,
            models.BOARD_KEY,
            models.DEFCONFIG_KEY,
            models.JOB_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
            models.VERSION_KEY
        ],
        models.ACCEPTED_KEYS: [
            models.ARCHITECTURE_KEY,
            models.BOARD_INSTANCE_KEY,
            models.BOARD_KEY,
            models.BOOT_LOAD_ADDR_KEY,
            models.BOOT_LOG_HTML_KEY,
            models.BOOT_LOG_KEY,
            models.BOOT_RESULT_DESC_KEY,
            models.BOOT_RESULT_KEY,
            models.BOOT_RETRIES_KEY,
            models.BOOT_TIME_KEY,
            models.BOOT_WARNINGS_KEY,
            models.DEFCONFIG_FULL_KEY,
            models.DEFCONFIG_KEY,
            models.DTB_ADDR_KEY,
            models.DTB_APPEND_KEY,
            models.DTB_KEY,
            models.EMAIL_KEY,
            models.ENDIANNESS_KEY,
            models.FASTBOOT_CMD_KEY,
            models.FASTBOOT_KEY,
            models.FILE_SERVER_RESOURCE_KEY,
            models.FILE_SERVER_URL_KEY,
            models.GIT_BRANCH_KEY,
            models.GIT_COMMIT_KEY,
            models.GIT_DESCRIBE_KEY,
            models.GIT_URL_KEY,
            models.ID_KEY,
            models.INITRD_ADDR_KEY,
            models.INITRD_KEY,
            models.JOB_KEY,
            models.KERNEL_IMAGE_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
            models.MACH_KEY,
            models.METADATA_KEY,
            models.NAME_KEY,
            models.QEMU_COMMAND_KEY,
            models.QEMU_KEY,
            models.STATUS_KEY,
            models.UIMAGE_ADDR_KEY,
            models.UIMAGE_KEY,
            models.VERSION_KEY
        ]
    },
    "GET": [
        models.ARCHITECTURE_KEY,
        models.BOARD_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.ENDIANNESS_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_COMMIT_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.LAB_NAME_KEY,
        models.MACH_KEY,
        models.NAME_KEY,
        models.RETRIES_KEY,
        models.STATUS_KEY,
        models.WARNINGS_KEY
    ],
    "DELETE": [
        models.BOARD_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
    ]
}

COUNT_VALID_KEYS = {
    "GET": [
        models.ARCHITECTURE_KEY,
        models.BOARD_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.ERRORS_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_COMMIT_KEY,
        models.GIT_DESCRIBE_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_CONFIG_KEY,
        models.KERNEL_IMAGE_KEY,
        models.KERNEL_KEY,
        models.MODULES_DIR_KEY,
        models.MODULES_KEY,
        models.NAME_KEY,
        models.PRIVATE_KEY,
        models.STATUS_KEY,
        models.SYSTEM_MAP_KEY,
        models.TEXT_OFFSET_KEY,
        models.TIME_KEY,
        models.WARNINGS_KEY,
    ],
}

DEFCONFIG_VALID_KEYS = {
    "GET": [
        models.ARCHITECTURE_KEY,
        models.BUILD_LOG_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_KEY,
        models.DIRNAME_KEY,
        models.ERRORS_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_COMMIT_KEY,
        models.GIT_DESCRIBE_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KCONFIG_FRAGMENTS_KEY,
        models.KERNEL_CONFIG_KEY,
        models.KERNEL_IMAGE_KEY,
        models.KERNEL_KEY,
        models.MODULES_DIR_KEY,
        models.MODULES_KEY,
        models.NAME_KEY,
        models.STATUS_KEY,
        models.SYSTEM_MAP_KEY,
        models.TEXT_OFFSET_KEY,
        models.WARNINGS_KEY,
    ],
}

TOKEN_VALID_KEYS = {
    "POST": [
        models.ADMIN_KEY,
        models.DELETE_KEY,
        models.EMAIL_KEY,
        models.EXPIRED_KEY,
        models.EXPIRES_KEY,
        models.GET_KEY,
        models.IP_ADDRESS_KEY,
        models.IP_RESTRICTED,
        models.LAB_KEY,
        models.NAME_KEY,
        models.POST_KEY,
        models.SUPERUSER_KEY,
        models.TEST_LAB_KEY,
        models.UPLOAD_KEY,
        models.USERNAME_KEY,
        models.VERSION_KEY
    ],
    "PUT": [
        models.ADMIN_KEY,
        models.DELETE_KEY,
        models.EMAIL_KEY,
        models.EXPIRED_KEY,
        models.EXPIRES_KEY,
        models.GET_KEY,
        models.IP_ADDRESS_KEY,
        models.IP_RESTRICTED,
        models.LAB_KEY,
        models.NAME_KEY,
        models.POST_KEY,
        models.SUPERUSER_KEY,
        models.TEST_LAB_KEY,
        models.UPLOAD_KEY,
        models.USERNAME_KEY,
        models.VERSION_KEY
    ],
    "GET": [
        models.CREATED_KEY,
        models.EMAIL_KEY,
        models.EXPIRED_KEY,
        models.EXPIRES_KEY,
        models.ID_KEY,
        models.IP_ADDRESS_KEY,
        models.NAME_KEY,
        models.PROPERTIES_KEY,
        models.TOKEN_KEY,
        models.USERNAME_KEY
    ],
}

SUBSCRIPTION_VALID_KEYS = {
    "GET": [
        models.JOB_KEY
    ],
    "POST": [
        models.EMAIL_KEY,
        models.JOB_KEY,
    ],
    "DELETE": [
        models.EMAIL_KEY
    ],
}

JOB_VALID_KEYS = {
    "POST": [
        models.JOB_KEY,
        models.KERNEL_KEY
    ],
    "GET": [
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
            models.VERSION_KEY,
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

REPORT_VALID_KEYS = {
    "GET": [
        models.CREATED_KEY,
        models.ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.NAME_KEY,
        models.STATUS_KEY,
        models.TYPE_KEY,
        models.UPDATED_KEY
    ]
}

SEND_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.JOB_KEY,
            models.KERNEL_KEY
        ],
        models.ACCEPTED_KEYS: [
            models.BOOT_REPORT_SEND_TO_KEY,
            models.BUILD_REPORT_SEND_TO_KEY,
            models.DELAY_KEY,
            models.EMAIL_FORMAT_KEY,
            models.JOB_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
            models.REPORT_SEND_TO_KEY,
            models.SEND_BOOT_REPORT_KEY,
            models.SEND_BUILD_REPORT_KEY
        ]
    }
}

BISECT_VALID_KEYS = {
    "GET": [
        models.BOOT_ID_KEY,
        models.COLLECTION_KEY,
        models.COMPARE_TO_KEY,
        models.DEFCONFIG_ID_KEY
    ]
}

TEST_SUITE_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.DEFCONFIG_ID_KEY,
            models.LAB_NAME_KEY,
            models.NAME_KEY,
            models.VERSION_KEY
        ],
        models.ACCEPTED_KEYS: [
            models.ARCHITECTURE_KEY,
            models.BOARD_INSTANCE_KEY,
            models.BOARD_KEY,
            models.BOOT_ID_KEY,
            models.CREATED_KEY,
            models.DEFCONFIG_FULL_KEY,
            models.DEFCONFIG_ID_KEY,
            models.DEFCONFIG_KEY,
            models.DEFINITION_URI_KEY,
            models.JOB_ID_KEY,
            models.JOB_KEY,
            models.KERNEL_KEY,
            models.LAB_NAME_KEY,
            models.METADATA_KEY,
            models.NAME_KEY,
            models.TEST_CASE_KEY,
            models.TEST_SET_KEY,
            models.VCS_COMMIT_KEY,
            models.VERSION_KEY
        ]
    },
    "PUT": [
        models.ARCHITECTURE_KEY,
        models.BOARD_INSTANCE_KEY,
        models.BOARD_KEY,
        models.BOOT_ID_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.DEFINITION_URI_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.METADATA_KEY,
        models.NAME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ],
    "GET": [
        models.ARCHITECTURE_KEY,
        models.BOARD_INSTANCE_KEY,
        models.BOARD_KEY,
        models.BOOT_ID_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.DEFINITION_URI_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.LAB_NAME_KEY,
        models.TIME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ]
}

TEST_SET_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.NAME_KEY,
            models.TEST_SUITE_ID_KEY,
            models.VERSION_KEY
        ],
        models.ACCEPTED_KEYS: [
            models.CREATED_KEY,
            models.DEFINITION_URI_KEY,
            models.METADATA_KEY,
            models.NAME_KEY,
            models.PARAMETERS_KEY,
            models.TEST_CASE_KEY,
            models.TEST_SUITE_ID_KEY,
            models.TIME_KEY,
            models.VCS_COMMIT_KEY,
            models.VERSION_KEY,
        ]
    },
    "PUT": [
        models.CREATED_KEY,
        models.DEFINITION_URI_KEY,
        models.NAME_KEY,
        models.PARAMETERS_KEY,
        models.TEST_SUITE_ID_KEY,
        models.TIME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ],
    "GET": [
        models.CREATED_KEY,
        models.DEFINITION_URI_KEY,
        models.NAME_KEY,
        models.PARAMETERS_KEY,
        models.TEST_SUITE_ID_KEY,
        models.TIME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ]
}

TEST_CASE_VALID_KEYS = {
    "POST": {
        models.MANDATORY_KEYS: [
            models.NAME_KEY,
            models.TEST_SUITE_ID_KEY,
            models.VERSION_KEY
        ],
        models.ACCEPTED_KEYS: [
            models.ATTACHMENTS_KEY,
            models.CREATED_KEY,
            models.DEFINITION_URI_KEY,
            models.KVM_GUEST_KEY,
            models.MAXIMUM_KEY,
            models.MEASUREMENTS_KEY,
            models.METADATA_KEY,
            models.MINIMUM_KEY,
            models.NAME_KEY,
            models.PARAMETERS_KEY,
            models.SAMPLES_KEY,
            models.SAMPLES_SQUARE_SUM_KEY,
            models.SAMPLES_SUM_KEY,
            models.STATUS_KEY,
            models.TEST_SET_ID_KEY,
            models.TEST_SUITE_ID_KEY,
            models.TIME_KEY,
            models.VCS_COMMIT_KEY,
            models.VERSION_KEY
        ]
    },
    "PUT": [
        models.ATTACHMENTS_KEY,
        models.CREATED_KEY,
        models.DEFINITION_URI_KEY,
        models.KVM_GUEST_KEY,
        models.MAXIMUM_KEY,
        models.MEASUREMENTS_KEY,
        models.METADATA_KEY,
        models.MINIMUM_KEY,
        models.NAME_KEY,
        models.PARAMETERS_KEY,
        models.SAMPLES_KEY,
        models.SAMPLES_SQUARE_SUM_KEY,
        models.SAMPLES_SUM_KEY,
        models.STATUS_KEY,
        models.TEST_SET_ID_KEY,
        models.TEST_SUITE_ID_KEY,
        models.TIME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ],
    "GET": [
        models.ATTACHMENTS_KEY,
        models.CREATED_KEY,
        models.DEFINITION_URI_KEY,
        models.KVM_GUEST_KEY,
        models.MAXIMUM_KEY,
        models.MEASUREMENTS_KEY,
        models.METADATA_KEY,
        models.MINIMUM_KEY,
        models.NAME_KEY,
        models.PARAMETERS_KEY,
        models.SAMPLES_KEY,
        models.SAMPLES_SQUARE_SUM_KEY,
        models.SAMPLES_SUM_KEY,
        models.STATUS_KEY,
        models.TEST_SET_ID_KEY,
        models.TEST_SUITE_ID_KEY,
        models.TIME_KEY,
        models.VCS_COMMIT_KEY,
        models.VERSION_KEY
    ]
}

ID_KEYS = [
    models.BOOT_ID_KEY,
    models.DEFCONFIG_ID_KEY,
    models.ID_KEY,
    models.JOB_ID_KEY,
    models.LAB_ID_KEY,
]

MASTER_KEY = "master_key"
API_TOKEN_HEADER = "Authorization"
ACCEPTED_CONTENT_TYPE = "application/json"
DEFAULT_RESPONSE_TYPE = "application/json; charset=UTF-8"
NOT_VALID_TOKEN = "Operation not permitted: check the token permissions"
METHOD_NOT_IMPLEMENTED = "Method not implemented"

MIDNIGHT = datetime.time(tzinfo=bson.tz_util.utc)
ALMOST_MIDNIGHT = datetime.time(23, 59, 59, tzinfo=bson.tz_util.utc)
EPOCH = datetime.datetime(1970, 1, 1, tzinfo=bson.tz_util.utc)


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

    created_on = get_created_on_date(query_args_func)
    add_created_on_date(spec, created_on)

    get_and_add_date_range(spec, query_args_func, created_on)
    get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
    update_id_fields(spec)

    sort = get_query_sort(query_args_func)
    fields = get_query_fields(query_args_func)
    skip, limit = get_skip_and_limit(query_args_func)
    unique = get_aggregate_value(query_args_func)

    return spec, sort, fields, skip, limit, unique


def get_trigger_query_values(query_args_func, valid_keys):
    """Handy function to get all the query args in a batch for trigger APIs.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: A list containing the valid keys that should be
    retrieved.
    :type valid_keys: list
    :return 6-tuple: spec, fields, skip, limit, compared.
    """
    spec = get_query_spec(query_args_func, valid_keys)

    created_on = get_created_on_date(query_args_func)
    add_created_on_date(spec, created_on)

    get_and_add_date_range(spec, query_args_func, created_on)
    get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
    update_id_fields(spec)

    sort = get_query_sort(query_args_func)
    fields = get_query_fields(query_args_func)
    skip, limit = get_skip_and_limit(query_args_func)
    compared = get_compared_value(query_args_func)

    return spec, sort, fields, skip, limit, compared


def _valid_value(value):
    """Make sure the passed value is valid for its type.

    This is necessary when value passed are like 0, False or similar and
    are actually valid values.

    :return True or False.
    """
    valid_value = True
    if isinstance(value, types.StringTypes):
        if value == "":
            valid_value = False
    elif isinstance(value, (types.ListType, types.TupleType)):
        if not value:
            valid_value = False
    elif value is None:
        valid_value = False
    return valid_value


def get_and_add_gte_lt_keys(spec, query_args_func, valid_keys):
    """Get the gte and lt query args values and add them to the spec.

    This is necessary to perform searches like 'greater than-equal' and
    'less-than'.

    :param spec: The spec data structure where to add the elements.
    :type spec: dict
    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :param valid_keys: The valid keys for this request.
    :type valid_keys: list
    """
    gte = query_args_func(models.GTE_KEY)
    lt = query_args_func(models.LT_KEY)
    spec_get = spec.get

    if all([gte, isinstance(gte, types.ListType)]):
        for arg in gte:
            _parse_and_add_gte_lt_value(
                arg, "$gte", valid_keys, spec, spec_get)
    elif gte and isinstance(gte, types.StringTypes):
        _parse_and_add_gte_lt_value(gte, "$gte", valid_keys, spec, spec_get)

    if all([lt, isinstance(lt, types.ListType)]):
        for arg in lt:
            _parse_and_add_gte_lt_value(arg, "$lt", valid_keys, spec, spec_get)
    elif all([lt, isinstance(lt, types.StringTypes)]):
        _parse_and_add_gte_lt_value(lt, "$lt", valid_keys, spec, spec_get)


def _parse_and_add_gte_lt_value(
        arg, operator, valid_keys, spec, spec_get_func=None):
    """Parse and add the provided query argument.

    Parse the argument looking for its value, and in case we have a valid value
    add it to the `spec` data structure.

    :param arg: The argument as retrieved from the request.
    :type arg: str
    :param operator: The operator to use, either '$gte' or '$lt'.
    :type operator: str
    :param valid_keys: The valid keys that this request can accept.
    :type valid_keys: list
    :param spec: The `spec` data structure where to store field-value.
    :type spec: dict
    :param spec_get_func: Optional get function of the spec data structure used
    to retrieve values from it.
    :type spec_get_func: function
    """
    field = value = None
    try:
        field, value = arg.split(",")
        if field not in valid_keys:
            field = None
            utils.LOG.warn(
                "Wrong field specified for '%s', got '%s'",
                operator, field)

        val_type = KEY_TYPES.get(field, None)
        if val_type and val_type == "int":
            try:
                value = int(value)
            except ValueError, ex:
                utils.LOG.error(
                    "Error converting value to %s: %s",
                    val_type, value)
                utils.LOG.exception(ex)
                value = None

        if all([field is not None, _valid_value(value)]):
            _add_gte_lt_value(
                field, value, operator, spec, spec_get_func)
    except ValueError, ex:
        error_msg = (
            "Wrong value specified for '%s' query argument: %s" %
            (operator, arg)
        )
        utils.LOG.error(error_msg)
        utils.LOG.exception(ex)


def _add_gte_lt_value(field, value, operator, spec, spec_get_func=None):
    """Add the field-value pair to the spec data structure.

    :param field: The field name.
    :type field: str
    :param value: The value of the field.
    :type value: str
    :param operator: The operator to use, either '$gte' or '$lt'.
    :type operator: str
    :param spec: The `spec` data structure where to store field-value.
    :type spec: dict
    :param spec_get_func: Optional get function of the spec data structure used
    to retrieve values from it.
    :type spec_get_func: function
    """
    if not spec_get_func:
        spec_get_func = spec.get

    prev_val = spec_get_func(field, None)
    new_key_val = {operator: value}

    if prev_val:
        prev_val.update(new_key_val)
    else:
        spec[field] = new_key_val


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
            try:
                spec[key] = bson.objectid.ObjectId(spec[key])
            except bson.errors.InvalidId, ex:
                # We remove the key since it won't serve anything good.
                utils.LOG.error(
                    "Wrong ObjectId value for key '%s', got '%s': ignoring",
                    key, spec[key])
                utils.LOG.exception(ex)
                spec.pop(key, None)


def get_aggregate_value(query_args_func):
    """Get the value of the aggregate key.

    :param query_args_func: A function used to return a list of the query
    arguments.
    :type query_args_func: function
    :return The aggregate value as string.
    """
    aggregate = query_args_func(models.AGGREGATE_KEY)
    if aggregate and isinstance(aggregate, types.ListType):
        aggregate = aggregate[-1]
    else:
        aggregate = None
    return aggregate


def get_compared_value(query_args_func):
    """Get the value of the compared key.

    This is used by the trigger API to determine if the results should be
    returned by comparing what other labs have already done.

    The `compared` key in the query arguments must be an integer, and it will
    be converted into a boolean. Other value types will be treated as False.

    If a list of `compared` key is retrieved, only the last one will be used.

    :param query_args_func: The function used to get the query arguments.
    :type query_args_func: function
    :return The compared value as boolean.
    """
    compared = query_args_func(models.COMPARED_KEY)
    if isinstance(compared, types.ListType):
        if compared:
            compared = compared[-1]

    if isinstance(compared, (types.StringTypes, types.IntType)):
        compared = bool(compared)
    else:
        compared = False

    return compared


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
        and multiple values. Makes sure also that the list of values is valid,
        meaning that we do not have None or empty values.

        :return A tuple with the key and its value.
        """
        val_type = None

        for key in valid_keys:
            val_type = KEY_TYPES.get(key, None)
            val = query_args_func(key) or []
            if val:
                # Go through the values and make sure we have valid ones.
                val = [v for v in val if _valid_value(v)]
                len_val = len(val)

                if len_val == 1:
                    if val_type and val_type == "int":
                        try:
                            val = int(val[0])
                        except ValueError, ex:
                            utils.LOG.error(
                                "Error converting value to %s: %s",
                                val_type, val[0])
                            utils.LOG.exception(ex)
                            val = []
                    else:
                        val = val[0]
                elif len_val > 1:
                    # More than one value, make sure we look for all of them.
                    if val_type and val_type == "int":
                        try:
                            val = {"$in": [int(v) for v in val]}
                        except ValueError, ex:
                            utils.LOG.error(
                                "Error converting list of values to %s: %s",
                                val_type, val)
                            utils.LOG.exception(ex)
                            val = []
                    else:
                        val = {"$in": val}

            yield key, val

    spec = {}
    if valid_keys and isinstance(valid_keys, types.ListType):
        spec = {
            k: v for k, v in [
                (key, val)
                for key, val in _get_spec_values()
                if _valid_value(val)
            ]
        }

    return spec


def get_created_on_date(query_args_func):
    """Retrieve the `created_on` key from the query args.

    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :return A `datetime.date` object or None.
    """
    created_on = query_args_func(models.CREATED_KEY)
    valid_date = None
    strptime_func = datetime.datetime.strptime

    if created_on:
        if isinstance(created_on, types.ListType):
            created_on = created_on[-1]

        if isinstance(created_on, types.StringTypes):
            try:
                valid_date = strptime_func(created_on, "%Y-%m-%d")
            except ValueError:
                try:
                    valid_date = strptime_func(created_on, "%Y%m%d")
                except ValueError:
                    utils.LOG.error(
                        "No valid value provided for '%s' key, got '%s'",
                        models.CREATED_KEY, created_on)
            if valid_date:
                valid_date = datetime.date(
                    valid_date.year, valid_date.month, valid_date.day)

    return valid_date


def add_created_on_date(spec, created_on):
    """Add the `created_on` key to the search spec data structure.

    :param spec: The dictionary where to store the key-value.
    :type spec: dictionary
    :param created_on: The `date` as passed in the query args.
    :type created_on: `datetime.date`
    :return The passed `spec` updated.
    """
    if all([created_on, isinstance(created_on, datetime.date)]):
        date_combine = datetime.datetime.combine

        start_date = date_combine(created_on, MIDNIGHT)
        end_date = date_combine(created_on, ALMOST_MIDNIGHT)

        spec[models.CREATED_KEY] = {
            "$gte": start_date, "$lt": end_date}
    else:
        # Remove the key if, by chance, it got into the spec with
        # previous iterations on the query args.
        if models.CREATED_KEY in spec.viewkeys():
            spec.pop(models.CREATED_KEY, None)

    return spec


def get_and_add_date_range(spec, query_args_func, created_on=None):
    """Retrieve the `date_range` query from the request.

    Add the retrieved `date_range` value into the provided `spec` data
    structure.

    :param spec: The dictionary where to store the key-value.
    :type spec: dictionary
    :param query_args_func: A function used to return a list of query
    arguments.
    :type query_args_func: function
    :param created_on: The `date` as passed in the query args.
    :type created_on: `datetime.date`
    :return The passed `spec` updated.
    """
    date_combine = datetime.datetime.combine
    date_range = query_args_func(models.DATE_RANGE_KEY)

    if date_range:
        # Start date needs to be set at the end of the day!
        if created_on and isinstance(created_on, datetime.date):
            # If the created_on key is defined, along with the date_range one
            # we combine the both and calculate a date_range from the provided
            # values. created_on must be a `date` object.
            today = date_combine(created_on, ALMOST_MIDNIGHT)
        else:
            today = date_combine(datetime.date.today(), ALMOST_MIDNIGHT)

        previous = calculate_date_range(date_range, created_on)

        spec[models.CREATED_KEY] = {"$gte": previous, "$lt": today}
    return spec


def calculate_date_range(date_range, created_on=None):
    """Calculate the new date subtracting the passed number of days.

    It removes the passed days from today date, calculated at midnight
    UTC.

    :param date_range: The number of days to remove from today.
    :type date_range int, long, str
    :return A new `datetime.date` object that is the result of the
    subtraction of `datetime.date.today()` and
    `datetime.timedelta(days=date_range)`.
    """
    date_timedelta = datetime.timedelta
    date_combine = datetime.datetime.combine

    if isinstance(date_range, types.ListType):
        date_range = date_range[-1]

    if isinstance(date_range, types.StringTypes):
        try:
            date_range = int(date_range)
        except ValueError:
            utils.LOG.error(
                "Wrong value passed to date_range: %s", date_range)
            date_range = DEFAULT_DATE_RANGE

    date_range = abs(date_range)
    if date_range > date_timedelta.max.days:
        date_range = DEFAULT_DATE_RANGE

    # Calcuate with midnight in mind though, so we get the starting of
    # the day for the previous date.
    if created_on and isinstance(created_on, datetime.date):
        today = date_combine(created_on, MIDNIGHT)
    else:
        today = date_combine(datetime.date.today(), MIDNIGHT)
    delta = date_timedelta(days=date_range)

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
        query_args_func, [models.FIELD_KEY, models.NOT_FIELD_KEY])

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
        query_args_func, [models.SORT_KEY, models.SORT_ORDER_KEY])

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

    For DELETE requests, if the token is a lab token, the request will be
    refused. The lab token can be used only to delete boot reports.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([(method == "POST" or method == "PUT"), token.is_post_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_delete_token]):
        if not token.is_lab_token:
            valid_token = True

    return valid_token


def valid_token_bh(token, method):
    """Make sure the token is a valid token for the `BootHandler`.

    This is a special case to handle a lab token (token associeated with a lab)

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([(method == "POST" or method == "PUT"), token.is_post_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_delete_token]):
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
    elif all([token.is_superuser, method == "GET"]):
        valid_token = True

    return valid_token


def valid_token_upload(token, method):
    """Make sure a token is enabled to upload files.

    :param token: The token object to validate.
    :param method: The HTTP method this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if any([token.is_admin, token.is_superuser]):
        valid_token = True
    if all([(method == "PUT" or method == "POST"), token.is_upload_token]):
        valid_token = True

    return valid_token


def valid_token_tests(token, method):
    """Make sure a token is enabled for test reports.

    :param token: The token object to validate.
    :param method: The HTTP method this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if any([token.is_admin, token.is_superuser]):
        valid_token = True
    elif all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([method == "PUT" or method == "POST", token.is_test_lab_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_test_lab_token]):
        valid_token = True

    return valid_token


def validate_token(token_obj, method, remote_ip, validate_func):
    """Make sure the passed token is valid.

    :param token_obj: The JSON object from the db that contains the token.
    :param method: The HTTP verb this token is being validated for.
    :param remote_ip: The remote IP address sending the token.
    :param validate_func: Function called to validate the token, must accept
        a Token object and the method string.
    :return A 2-tuple: True or False; the token object.
    """
    valid_token = True
    token = None

    if token_obj:
        token = mtoken.Token.from_json(token_obj)

        if not isinstance(token, mtoken.Token):
            utils.LOG.error("Retrieved token is not a Token object")
            valid_token = False
        else:
            if _is_expired_token(token):
                valid_token = False
            else:
                valid_token &= validate_func(token, method)

                if all([valid_token,
                        token.is_ip_restricted,
                        not _valid_token_ip(token, remote_ip)]):
                    valid_token = False
    else:
        valid_token = False

    return valid_token, token


def _is_expired_token(token):
    """Verify whther a token is expired or not.

    :param token: The token to verify.
    :type token: `models.Token`.
    :return True or False.
    """
    is_expired = False
    if token.expired:
        is_expired = True
    else:
        expires_on = token.expires_on
        if (expires_on is not None and
                isinstance(expires_on, datetime.datetime)):
            if expires_on < datetime.datetime.now():
                is_expired = True

    return is_expired


def _valid_token_ip(token, remote_ip):
    """Make sure the token comes from the designated IP addresses.

    :param token: The Token object to validate.
    :param remote_ip: The remote IP address sending the token.
    :return True or False.
    """
    valid_token = False

    if token.ip_address is not None:
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
            utils.LOG.info(
                "No remote IP address provided, cannot validate token")
    else:
        valid_token = True

    return valid_token
