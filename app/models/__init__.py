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

# The default mongodb database name.
DB_NAME = "kernel-ci"

DEFAULT_SCHEMA_VERSION = "1.0"

# i18n domain name.
I18N_DOMAIN = "kernelci-backend"

# The default ID key, and other keys, for mongodb documents and queries.
ACCEPTED_KEYS = "accepted"
ADDRESS_KEY = "address"
AGGREGATE_KEY = "aggregate"
ARCHITECTURE_KEY = "arch"
ATTACHMENTS_KEY = "attachments"
BASELINE_KEY = "baseline"
BOARD_INSTANCE_KEY = "board_instance"
BOARD_KEY = "board"
BOOTLOADER_TYPE_KEY = "bootloader"
BOOTLOADER_VERSION_KEY = "bootloader_version"
BOOT_ID_KEY = "boot_id"
BOOT_JOB_ID_KEY = "boot_job_id"
BOOT_JOB_PATH_KEY = "boot_job_path"
BOOT_JOB_URL_KEY = "boot_job_url"
BOOT_LOAD_ADDR_KEY = "loadaddr"
BOOT_LOG_HTML_KEY = "boot_log_html"
BOOT_LOG_KEY = "boot_log"
BOOT_REGRESSIONS_ID_KEY = "boot_regressions_id"
BOOT_RESULT_DESC_KEY = "boot_result_description"
BOOT_RESULT_KEY = "boot_result"
BOOT_RETRIES_KEY = "boot_retries"
BOOT_TIME_KEY = "boot_time"
BOOT_WARNINGS_KEY = "boot_warnings"
BUILD_COUNTS_KEY = "build_counts"
BUILD_ERRORS_KEY = "build_errors"
BUILD_ID_KEY = "build_id"
BUILD_LOG_KEY = "build_log"
BUILD_LOG_SIZE_KEY = "build_log_size"
BUILD_PLATFORM_KEY = "build_platform"
BUILD_RESULT_KEY = "build_result"
BUILD_TIME_KEY = "build_time"
BUILD_TYPE_KEY = "build_type"
BUILD_WARNINGS_KEY = "build_warnings"
CHAINLOADER_TYPE_KEY = "chainloader"
COMPARED_KEY = "compared"
COMPARE_TO_KEY = "compare_to"
COMPILER_KEY = "compiler"
BUILD_ENVIRONMENT_KEY = "build_environment"
COMPILER_VERSION_EXT_KEY = "compiler_version_ext"
COMPILER_VERSION_FULL_KEY = "compiler_version_full"
COMPILER_VERSION_KEY = "compiler_version"
CONTACT_KEY = "contact"
COUNT_KEY = "count"
CREATED_KEY = "created_on"
CROSS_COMPILE_KEY = "cross_compile"
DATE_RANGE_KEY = "date_range"
DEFCONFIG_FULL_KEY = "defconfig_full"
DEFCONFIG_KEY = "defconfig"
DEFECTS_KEY = "defects"
DEFECT_ACK_KEY = "defect_ack"
DEFECT_COMMENT_KEY = "defect_comment"
DEFECT_URL_KEY = "defect_url"
DEFINITION_URI_KEY = "definition_uri"
DELTA_RESULT_KEY = "delta_result"
DEVICE_TYPE_KEY = "device_type"
DIRNAME_KEY = "dirname"
DIRECTORY_PATH = "directory_path"
DOC_ID_KEY = "doc_id"
DTB_ADDR_KEY = "dtb_addr"
DTB_APPEND_KEY = "dtb_append"
DTB_DIR_DATA_KEY = "dtb_dir_data"
DTB_DIR_KEY = "dtb_dir"
DTB_KEY = "dtb"
EMAIL_FORMAT_KEY = "format"
EMAIL_HTML_FORMAT_KEY = "html"
EMAIL_KEY = "email"
EMAIL_LIST_KEY = "emails"
EMAIL_TXT_FORMAT_KEY = "txt"
ENDIANNESS_KEY = "endian"
ERRORS_COUNT_KEY = "errors_count"
ERRORS_KEY = "errors"
EXPIRED_KEY = "expired"
EXPIRES_KEY = "expires_on"
FASTBOOT_CMD_KEY = "fastboot_cmd"
FASTBOOT_KEY = "fastboot"
FIELD_KEY = "field"
FILESYSTEM_TYPE_KEY = "filesystem"
FILE_SERVER_RESOURCE_KEY = "file_server_resource"
FILE_SERVER_URL_KEY = "file_server_url"
GIT_BRANCH_KEY = "git_branch"
GIT_COMMIT_KEY = "git_commit"
GIT_DESCRIBE_KEY = "git_describe"
GIT_DESCRIBE_V_KEY = "git_describe_v"
GIT_URL_KEY = "git_url"
GTE_KEY = "gte"
HIERARCHY_KEY = "hierarchy"
ID_KEY = "_id"
IMAGE_TYPE_KEY = "image_type"
INDEX_KEY = "index"
INITRD_ADDR_KEY = "initrd_addr"
INITRD_INFO_KEY = "initrd_info"
INITRD_KEY = "initrd"
IP_ADDRESS_KEY = "ip_address"
JOB_ID_KEY = "job_id"
JOB_KEY = "job"
KCONFIG_FRAGMENTS_KEY = "kconfig_fragments"
KERNEL_CONFIG_KEY = "kernel_config"
KERNEL_CONFIG_SIZE_KEY = "kernel_config_size"
KERNEL_IMAGE_KEY = "kernel_image"
KERNEL_IMAGE_SIZE_KEY = "kernel_image_size"
KERNEL_KEY = "kernel"
KERNEL_VERSION_KEY = "kernel_version"
KVM_GUEST_KEY = "kvm_guest"
LAB_ID_KEY = "lab_id"
LAB_NAME_KEY = "lab_name"
LIMIT_KEY = "limit"
LOAD_ADDR_KEY = "load_addr"
LT_KEY = "lt"
MACH_ALIAS_KEY = "mach_alias"
MACH_KEY = "mach"
MANDATORY_KEYS = "mandatory"
MAXIMUM_KEY = "maximum"
MEASUREMENTS_KEY = "measurements"
METADATA_KEY = "metadata"
MINIMUM_KEY = "minimum"
MISMATCHES_COUNT_KEY = "mismatches_count"
MISMATCHES_KEY = "mismatches"
MODULES_DIR_KEY = "modules_dir"
MODULES_KEY = "modules"
MODULES_SIZE_KEY = "modules_size"
NAME_KEY = "name"
NOT_FIELD_KEY = "nfield"
PARAMETERS_KEY = "parameters"
PARENT_ID_KEY = "parent_id"
PLAN_KEY = "plan"
PRIVATE_KEY = "private"
PROPERTIES_KEY = "properties"
QEMU_COMMAND_KEY = "qemu_command"
QEMU_KEY = "qemu"
RESULT_KEY = "result"
RETRIES_KEY = "retries"
SAMPLES_KEY = "samples"
SAMPLES_SQUARE_SUM_KEY = "samples_sqr_sum"
SAMPLES_SUM_KEY = "samples_sum"
SKIP_KEY = "skip"
SORT_KEY = "sort"
SORT_ORDER_KEY = "sort_order"
START_DATE_KEY = "start_date"
STATUS_KEY = "status"
SUB_GROUPS_KEY = "sub_groups"
SUBJECT_KEY = "subject"
SURNAME_KEY = "surname"
SYSTEM_MAP_KEY = "system_map"
SYSTEM_MAP_SIZE_KEY = "system_map_size"
TEST_CASE_ID_KEY = "test_case_id"
TEST_CASES_KEY = "test_cases"
TEST_JOB_ID_KEY = "test_job_id"
TEST_JOB_PATH_KEY = "test_job_path"
TEST_JOB_URL_KEY = "test_job_url"
TEST_GROUP_ID_KEY = "test_group_id"
TEST_GROUP_NAME_KEY = "test_group_name"
TEXT_OFFSET_KEY = "text_offset"
TIME_KEY = "time"
TIME_RANGE_KEY = "time_range"
TOKEN_KEY = "token"
TOTAL_BUILDS_KEY = "total_builds"
TYPE_KEY = "type"
UIMAGE_ADDR_KEY = "uimage_addr"
UIMAGE_KEY = "uimage"
UPDATED_KEY = "updated_on"
USERNAME_KEY = "username"
REGRESSIONS_KEY = "regressions"
VCS_COMMIT_KEY = "vcs_commit"
VERSION_FULL_KEY = "full_version"
VERSION_KEY = "version"
VMLINUX_BSS_SIZE_KEY = "vmlinux_bss_size"
VMLINUX_DATA_SIZE_KEY = "vmlinux_data_size"
VMLINUX_FILE_KEY = "vmlinux_file"
VMLINUX_FILE_SIZE_KEY = "vmlinux_file_size"
VMLINUX_TEXT_SIZE_KEY = "vmlinux_text_size"
WARNINGS_COUNT_KEY = "warnings_count"
WARNINGS_KEY = "warnings"

# Email reporting control fields.
SEND_BOOT_REPORT_KEY = "boot_report"
SEND_BUILD_REPORT_KEY = "build_report"
REPORT_TYPE_KEY = "report_type"
REPORT_SEND_TO_KEY = "send_to"
REPORT_CC_KEY = "send_cc"
REPORT_BCC_KEY = "send_bcc"
DELAY_KEY = "delay"
IN_REPLY_TO_KEY = "in_reply_to"
PLAN_KEY = "plan"

# Token special fields.
ADMIN_KEY = "admin"
DELETE_KEY = "delete"
GET_KEY = "get"
IP_RESTRICTED = "ip_restricted"
LAB_KEY = "lab"
POST_KEY = "post"
PUT_KEY = "put"
SUPERUSER_KEY = "superuser"
TEST_LAB_KEY = "test_lab"
UPLOAD_KEY = "upload"

# Job and/or build status.
BUILD_STATUS = "BUILD"
ERROR_STATUS = "ERROR"
FAIL_STATUS = "FAIL"
OFFLINE_STATUS = "OFFLINE"
PASS_STATUS = "PASS"
SENT_STATUS = "SENT"
UNKNOWN_STATUS = "UNKNOWN"
UNTRIED_STATUS = "UNTRIED"
SKIP_STATUS = "SKIP"

# Build file names.
DONE_FILE = ".done"
DONE_FILE_PATTERN = "*.done"
BUILD_META_FILE = "build.meta"
BUILD_META_JSON_FILE = "build.json"
BUILD_FAIL_FILE = "build.FAIL"
BUILD_PASS_FILE = "build.PASS"

# Batch operation related keys.
BATCH_KEY = "batch"
METHOD_KEY = "method"
COLLECTION_KEY = "collection"
RESOURCE_KEY = "resource"
DOCUMENT_ID_KEY = "document_id"
DOCUMENT_KEY = "document"
QUERY_KEY = "query"
OP_ID_KEY = "operation_id"
DISTINCT_KEY = "distinct"
UNIQUE_KEY = "unique"

# Collection names.
BOOT_COLLECTION = "boot"
BOOT_REGRESSIONS_BY_BOOT_COLLECTION = "boot_regressions_by_boot_id"
BOOT_REGRESSIONS_COLLECTION = "boot_regressions"
BUILD_COLLECTION = "build"
COUNT_COLLECTION = "count"
JOB_COLLECTION = "job"
TOKEN_COLLECTION = "api-token"
BISECT_COLLECTION = "bisect"
LAB_COLLECTION = "lab"
REPORT_COLLECTION = "report"
UPLOAD_COLLECTION = "upload"
TEST_GROUP_COLLECTION = "test_group"
TEST_CASE_COLLECTION = "test_case"
TEST_REGRESSION_COLLECTION = "test_regression"
ERROR_LOGS_COLLECTION = "error_logs"
ERRORS_SUMMARY_COLLECTION = "errors_summary"
DAILY_STATS_COLLECTION = "daily_stats"
# Delta collections.
JOB_DELTA_COLLECTION = "job_delta"
BUILD_DELTA_COLLECTION = "build_delta"
BOOT_DELTA_COLLECTION = "boot_delta"

# Build types.
KERNEL_BUILD_TYPE = "kernel"

# Report types.
BUILD_REPORT = "build"
BOOT_REPORT = "boot"
BISECT_REPORT = "bisect"
TEST_REPORT = "test"

# Bisect values.
BISECT_BOOT_STATUS_KEY = "boot_status"
BISECT_BOOT_CREATED_KEY = "boot_created_on"
BISECT_BOOT_METADATA_KEY = "boot_metadata"
BISECT_DEFCONFIG_STATUS_KEY = "build_status"
BISECT_DEFCONFIG_CREATED_KEY = "build_created_on"
BISECT_DEFCONFIG_METADATA_KEY = "build_metadata"
BISECT_DEFCONFIG_ARCHITECTURE_KEY = "build_arch"
BISECT_DATA_KEY = "bisect_data"
BISECT_GOOD_COMMIT_KEY = "good_commit"
BISECT_BAD_COMMIT_KEY = "bad_commit"
BISECT_GOOD_COMMIT_DATE = "good_commit_date"
BISECT_BAD_COMMIT_DATE = "bad_commit_date"
BISECT_GOOD_COMMIT_URL = "good_commit_url"
BISECT_BAD_COMMIT_URL = "bad_commit_url"
BISECT_GOOD_SUMMARY_KEY = "good_summary"
BISECT_BAD_SUMMARY_KEY = "bad_summary"
BISECT_FOUND_SUMMARY_KEY = "found_summary"
BISECT_CHECKS_KEY = "checks"
BISECT_LOG_KEY = "log"

# LAVA Callback keys
LAVA_DEFINITION_KEY = "definition"
LAVA_DESCRIPTION_KEY = "description"
LAVA_START_TIME_KEY = "start_time"
LAVA_STATUS_STR_KEY = "status_string"
LAVA_RESULTS_KEY = "results"
LAVA_SUBMITTER_KEY = "submitter_username"
LAVA_ID_KEY = "id"
LAVA_PRIORITY_KEY = "priority"
LAVA_END_TIME_KEY = "end_time"
LAVA_SUBMIT_TIME_KEY = "submit_time"
LAVA_IS_PIPELINE_KEY = "is_pipeline"
LAVA_METADATA_KEY = "metadata"
LAVA_FAILURE_COMMENT_KEY = "failure_comment"
LAVA_DEVICE_ID_KEY = "actual_device_id"
LAVA_LOG_KEY = "log"

# Valid build status.
VALID_BUILD_STATUS = [
    BUILD_STATUS,
    FAIL_STATUS,
    PASS_STATUS,
    UNKNOWN_STATUS
]

# Valid boot status.
VALID_BOOT_STATUS = [
    FAIL_STATUS,
    OFFLINE_STATUS,
    PASS_STATUS,
    UNTRIED_STATUS
]

# Valid job status.
VALID_JOB_STATUS = [
    BUILD_STATUS,
    FAIL_STATUS,
    PASS_STATUS,
    UNKNOWN_STATUS
]

# Valid test case status.
VALID_TEST_CASE_STATUS = [
    ERROR_STATUS,
    FAIL_STATUS,
    PASS_STATUS,
    SKIP_STATUS
]

# The valid collections for the bisect handler.
BISECT_VALID_COLLECTIONS = [
    BOOT_COLLECTION,
    BUILD_COLLECTION
]

VALID_EMAIL_FORMATS = [
    EMAIL_HTML_FORMAT_KEY,
    EMAIL_TXT_FORMAT_KEY
]

# List of all available collections.
COLLECTIONS = [
    BOOT_COLLECTION,
    BUILD_COLLECTION,
    COUNT_COLLECTION,
    DAILY_STATS_COLLECTION,
    JOB_COLLECTION,
    TEST_CASE_COLLECTION,
    TEST_GROUP_COLLECTION
]

# Slightly different then above: this is used only for the /count API.
COUNT_COLLECTIONS = [
    BOOT_COLLECTION,
    BUILD_COLLECTION,
    JOB_COLLECTION,
    TEST_CASE_COLLECTION,
    TEST_GROUP_COLLECTION
]

# Handlers valid keys.
COUNT_VALID_KEYS = {
    "GET": [
        ARCHITECTURE_KEY,
        BOARD_INSTANCE_KEY,
        BOARD_KEY,
        BOOT_ID_KEY,
        BUILD_ID_KEY,
        COMPILER_KEY,
        COMPILER_VERSION_EXT_KEY,
        COMPILER_VERSION_KEY,
        CREATED_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        DEFINITION_URI_KEY,
        ERRORS_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        ID_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_CONFIG_KEY,
        KERNEL_IMAGE_KEY,
        KERNEL_KEY,
        LAB_NAME_KEY,
        MACH_KEY,
        MODULES_DIR_KEY,
        MODULES_KEY,
        NAME_KEY,
        PRIVATE_KEY,
        STATUS_KEY,
        SYSTEM_MAP_KEY,
        TEST_CASE_ID_KEY,
        TEST_JOB_ID_KEY,
        TEST_JOB_URL_KEY,
        TEST_GROUP_ID_KEY,
        TEST_GROUP_NAME_KEY,
        TEXT_OFFSET_KEY,
        TIME_KEY,
        TIME_KEY,
        VCS_COMMIT_KEY,
        VERSION_KEY,
        WARNINGS_KEY,
    ]
}

BOOT_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            ARCHITECTURE_KEY,
            BOARD_KEY,
            DEFCONFIG_KEY,
            GIT_BRANCH_KEY,
            JOB_KEY,
            KERNEL_KEY,
            LAB_NAME_KEY,
            VERSION_KEY,
            BUILD_ENVIRONMENT_KEY
        ],
        ACCEPTED_KEYS: [
            ARCHITECTURE_KEY,
            BOARD_INSTANCE_KEY,
            BOARD_KEY,
            BOOTLOADER_TYPE_KEY,
            BOOTLOADER_VERSION_KEY,
            BOOT_JOB_ID_KEY,
            BOOT_JOB_PATH_KEY,
            BOOT_JOB_URL_KEY,
            BOOT_LOAD_ADDR_KEY,
            BOOT_LOG_HTML_KEY,
            BOOT_LOG_KEY,
            BOOT_RESULT_DESC_KEY,
            BOOT_RESULT_KEY,
            BOOT_RETRIES_KEY,
            BOOT_TIME_KEY,
            BOOT_WARNINGS_KEY,
            BUILD_ENVIRONMENT_KEY,
            CHAINLOADER_TYPE_KEY,
            COMPILER_KEY,
            COMPILER_VERSION_EXT_KEY,
            COMPILER_VERSION_KEY,
            DEFCONFIG_FULL_KEY,
            DEFCONFIG_KEY,
            DTB_ADDR_KEY,
            DTB_APPEND_KEY,
            DTB_KEY,
            EMAIL_KEY,
            ENDIANNESS_KEY,
            FASTBOOT_CMD_KEY,
            FASTBOOT_KEY,
            FILESYSTEM_TYPE_KEY,
            FILE_SERVER_RESOURCE_KEY,
            FILE_SERVER_URL_KEY,
            GIT_BRANCH_KEY,
            GIT_COMMIT_KEY,
            GIT_DESCRIBE_KEY,
            GIT_URL_KEY,
            ID_KEY,
            IMAGE_TYPE_KEY,
            INITRD_ADDR_KEY,
            INITRD_KEY,
            JOB_KEY,
            KERNEL_IMAGE_KEY,
            KERNEL_IMAGE_SIZE_KEY,
            KERNEL_KEY,
            LAB_NAME_KEY,
            MACH_KEY,
            METADATA_KEY,
            QEMU_COMMAND_KEY,
            QEMU_KEY,
            STATUS_KEY,
            UIMAGE_ADDR_KEY,
            UIMAGE_KEY,
            VERSION_KEY
        ]
    },
    "GET": [
        ARCHITECTURE_KEY,
        BOARD_KEY,
        BOOTLOADER_TYPE_KEY,
        BOOTLOADER_VERSION_KEY,
        BOOT_JOB_ID_KEY,
        BOOT_JOB_URL_KEY,
        BUILD_ENVIRONMENT_KEY,
        BUILD_ID_KEY,
        CHAINLOADER_TYPE_KEY,
        COMPILER_KEY,
        COMPILER_VERSION_KEY,
        CREATED_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        ENDIANNESS_KEY,
        FILESYSTEM_TYPE_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        GIT_URL_KEY,
        ID_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_IMAGE_KEY,
        KERNEL_IMAGE_SIZE_KEY,
        KERNEL_KEY,
        LAB_NAME_KEY,
        MACH_KEY,
        RETRIES_KEY,
        STATUS_KEY,
        WARNINGS_KEY
    ],
    "DELETE": [
        BOARD_KEY,
        BOOT_JOB_ID_KEY,
        BOOT_JOB_URL_KEY,
        DEFCONFIG_FULL_KEY,
        BUILD_ID_KEY,
        DEFCONFIG_KEY,
        ID_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
    ]
}

BUILD_VALID_KEYS = {
    "GET": [
        ARCHITECTURE_KEY,
        BUILD_LOG_KEY,
        BUILD_LOG_SIZE_KEY,
        BUILD_TYPE_KEY,
        COMPILER_KEY,
        BUILD_ENVIRONMENT_KEY,
        COMPILER_VERSION_KEY,
        CREATED_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        DIRNAME_KEY,
        ERRORS_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        ID_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KCONFIG_FRAGMENTS_KEY,
        KERNEL_CONFIG_KEY,
        KERNEL_CONFIG_SIZE_KEY,
        KERNEL_IMAGE_KEY,
        KERNEL_IMAGE_SIZE_KEY,
        KERNEL_KEY,
        KERNEL_VERSION_KEY,
        MODULES_DIR_KEY,
        MODULES_KEY,
        MODULES_SIZE_KEY,
        STATUS_KEY,
        SYSTEM_MAP_KEY,
        SYSTEM_MAP_SIZE_KEY,
        TEXT_OFFSET_KEY,
        WARNINGS_KEY
    ],
    "POST": {
        MANDATORY_KEYS: [
            ARCHITECTURE_KEY,
            BUILD_ENVIRONMENT_KEY,
            DEFCONFIG_KEY,
            GIT_BRANCH_KEY,
            JOB_KEY,
            KERNEL_KEY
        ],
        ACCEPTED_KEYS: [
            ARCHITECTURE_KEY,
            BUILD_ENVIRONMENT_KEY,
            DEFCONFIG_FULL_KEY,
            DEFCONFIG_KEY,
            GIT_BRANCH_KEY,
            JOB_KEY,
            KERNEL_KEY,
            KERNEL_VERSION_KEY,
            VERSION_KEY
        ]
    }
}

TOKEN_VALID_KEYS = {
    "POST": [
        ADMIN_KEY,
        DELETE_KEY,
        EMAIL_KEY,
        EXPIRED_KEY,
        EXPIRES_KEY,
        GET_KEY,
        IP_ADDRESS_KEY,
        IP_RESTRICTED,
        LAB_KEY,
        POST_KEY,
        SUPERUSER_KEY,
        TEST_LAB_KEY,
        UPLOAD_KEY,
        USERNAME_KEY,
        VERSION_KEY
    ],
    "PUT": [
        ADMIN_KEY,
        DELETE_KEY,
        EMAIL_KEY,
        EXPIRED_KEY,
        EXPIRES_KEY,
        GET_KEY,
        IP_ADDRESS_KEY,
        IP_RESTRICTED,
        LAB_KEY,
        POST_KEY,
        SUPERUSER_KEY,
        TEST_LAB_KEY,
        UPLOAD_KEY,
        USERNAME_KEY,
        VERSION_KEY
    ],
    "GET": [
        CREATED_KEY,
        EMAIL_KEY,
        EXPIRED_KEY,
        EXPIRES_KEY,
        ID_KEY,
        IP_ADDRESS_KEY,
        PROPERTIES_KEY,
        TOKEN_KEY,
        USERNAME_KEY
    ]
}

JOB_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            GIT_BRANCH_KEY,
            JOB_KEY,
            KERNEL_KEY
        ],
        ACCEPTED_KEYS: [
            GIT_BRANCH_KEY,
            GIT_COMMIT_KEY,
            GIT_DESCRIBE_KEY,
            JOB_KEY,
            KERNEL_KEY,
            KERNEL_VERSION_KEY,
            STATUS_KEY
        ]
    },
    "GET": [
        CREATED_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        KERNEL_VERSION_KEY,
        PRIVATE_KEY,
        STATUS_KEY
    ],
}

BATCH_VALID_KEYS = {
    "POST": [
        DISTINCT_KEY,
        DOCUMENT_KEY,
        METHOD_KEY,
        OP_ID_KEY,
        QUERY_KEY,
        RESOURCE_KEY
    ]
}

LAB_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            CONTACT_KEY,
            NAME_KEY
        ],
        ACCEPTED_KEYS: [
            ADDRESS_KEY,
            CONTACT_KEY,
            NAME_KEY,
            PRIVATE_KEY,
            TOKEN_KEY,
            VERSION_KEY
        ]
    },
    "PUT": [
        ADDRESS_KEY,
        CONTACT_KEY,
        NAME_KEY,
        PRIVATE_KEY,
        TOKEN_KEY,
        VERSION_KEY
    ],
    "GET": [
        ADDRESS_KEY,
        CONTACT_KEY,
        CREATED_KEY,
        ID_KEY,
        NAME_KEY,
        PRIVATE_KEY,
        TOKEN_KEY,
        UPDATED_KEY
    ],
    "DELETE": [
        ADDRESS_KEY,
        CONTACT_KEY,
        ID_KEY,
        NAME_KEY,
        TOKEN_KEY
    ]
}

REPORT_VALID_KEYS = {
    "GET": [
        CREATED_KEY,
        ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        NAME_KEY,
        STATUS_KEY,
        TYPE_KEY,
        UPDATED_KEY
    ]
}

SEND_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            GIT_BRANCH_KEY,
            JOB_KEY,
            KERNEL_KEY,
        ],
        ACCEPTED_KEYS: [
            DELAY_KEY,
            EMAIL_FORMAT_KEY,
            GIT_BRANCH_KEY,
            IN_REPLY_TO_KEY,
            JOB_KEY,
            KERNEL_KEY,
            LAB_NAME_KEY,
            PLAN_KEY,
            REPORT_TYPE_KEY,
            REPORT_BCC_KEY,
            REPORT_CC_KEY,
            REPORT_SEND_TO_KEY,
            SEND_BOOT_REPORT_KEY,
            SEND_BUILD_REPORT_KEY,
            SUBJECT_KEY,
            # Bisection keys
            TYPE_KEY,
            ARCHITECTURE_KEY,
            DEFCONFIG_FULL_KEY,
            BUILD_ENVIRONMENT_KEY,
            DEVICE_TYPE_KEY,
            BISECT_GOOD_COMMIT_KEY,
            BISECT_BAD_COMMIT_KEY,
            BISECT_LOG_KEY,
        ]
    }
}

BISECT_VALID_KEYS = {
    "GET": [
        BOOT_ID_KEY,
        COLLECTION_KEY,
        COMPARE_TO_KEY,
        BUILD_ID_KEY
    ],
    "POST": [
        TYPE_KEY,
        ARCHITECTURE_KEY,
        JOB_KEY,
        KERNEL_KEY,
        GIT_BRANCH_KEY,
        DEFCONFIG_FULL_KEY,
        BUILD_ENVIRONMENT_KEY,
        LAB_NAME_KEY,
        DEVICE_TYPE_KEY,
        BISECT_GOOD_COMMIT_KEY,
        BISECT_BAD_COMMIT_KEY,
        BISECT_GOOD_SUMMARY_KEY,
        BISECT_BAD_SUMMARY_KEY,
        BISECT_FOUND_SUMMARY_KEY,
        BISECT_LOG_KEY,
        BISECT_CHECKS_KEY,
    ],
}

TEST_GROUP_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            BUILD_ID_KEY,
            LAB_NAME_KEY,
            NAME_KEY,
            BUILD_ENVIRONMENT_KEY,
        ],
        ACCEPTED_KEYS: [
            ARCHITECTURE_KEY,
            BOARD_INSTANCE_KEY,
            BOARD_KEY,
            BOOT_ID_KEY,
            BUILD_ENVIRONMENT_KEY,
            CREATED_KEY,
            DEFCONFIG_FULL_KEY,
            BUILD_ID_KEY,
            DEFCONFIG_KEY,
            DEFINITION_URI_KEY,
            GIT_BRANCH_KEY,
            INITRD_KEY,
            INITRD_INFO_KEY,
            JOB_ID_KEY,
            JOB_KEY,
            KERNEL_KEY,
            LAB_NAME_KEY,
            METADATA_KEY,
            NAME_KEY,
            TEST_CASES_KEY,
            VCS_COMMIT_KEY,
            VERSION_KEY
        ]
    },
    "PUT": [
        ARCHITECTURE_KEY,
        BOARD_INSTANCE_KEY,
        BOARD_KEY,
        BOOT_ID_KEY,
        BUILD_ENVIRONMENT_KEY,
        CREATED_KEY,
        DEFCONFIG_FULL_KEY,
        BUILD_ID_KEY,
        DEFCONFIG_KEY,
        DEFINITION_URI_KEY,
        GIT_BRANCH_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        METADATA_KEY,
        NAME_KEY,
        VCS_COMMIT_KEY,
        VERSION_KEY
    ],
    "GET": [
        ARCHITECTURE_KEY,
        BOARD_INSTANCE_KEY,
        BOARD_KEY,
        BOOT_ID_KEY,
        BUILD_ENVIRONMENT_KEY,
        BUILD_ID_KEY,
        CREATED_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        DEFINITION_URI_KEY,
        GIT_BRANCH_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        LAB_NAME_KEY,
        NAME_KEY,
        TIME_KEY,
        VCS_COMMIT_KEY,
        VERSION_KEY
    ]
}

TEST_CASE_VALID_KEYS = {
    "POST": {
        MANDATORY_KEYS: [
            NAME_KEY,
            TEST_GROUP_ID_KEY
        ],
        ACCEPTED_KEYS: [
            ATTACHMENTS_KEY,
            CREATED_KEY,
            DEFINITION_URI_KEY,
            KVM_GUEST_KEY,
            INDEX_KEY,
            MAXIMUM_KEY,
            MEASUREMENTS_KEY,
            METADATA_KEY,
            MINIMUM_KEY,
            NAME_KEY,
            PARAMETERS_KEY,
            SAMPLES_KEY,
            SAMPLES_SQUARE_SUM_KEY,
            SAMPLES_SUM_KEY,
            STATUS_KEY,
            TEST_GROUP_ID_KEY,
            TEST_GROUP_NAME_KEY,
            TIME_KEY,
            VCS_COMMIT_KEY,
            VERSION_KEY
        ]
    },
    "PUT": [
        ATTACHMENTS_KEY,
        CREATED_KEY,
        DEFINITION_URI_KEY,
        KVM_GUEST_KEY,
        INDEX_KEY,
        MAXIMUM_KEY,
        MEASUREMENTS_KEY,
        METADATA_KEY,
        MINIMUM_KEY,
        NAME_KEY,
        PARAMETERS_KEY,
        SAMPLES_KEY,
        SAMPLES_SQUARE_SUM_KEY,
        SAMPLES_SUM_KEY,
        STATUS_KEY,
        TEST_GROUP_ID_KEY,
        TEST_GROUP_NAME_KEY,
        TIME_KEY,
        VCS_COMMIT_KEY,
        VERSION_KEY
    ],
    "GET": [
        CREATED_KEY,
        DEFINITION_URI_KEY,
        KVM_GUEST_KEY,
        INDEX_KEY,
        MAXIMUM_KEY,
        MINIMUM_KEY,
        NAME_KEY,
        SAMPLES_KEY,
        STATUS_KEY,
        TEST_GROUP_ID_KEY,
        TEST_GROUP_NAME_KEY,
        TIME_KEY,
        VCS_COMMIT_KEY,
        VERSION_KEY
    ]
}

STATISTICS_VALID_KEYS = {
    "GET": [
        CREATED_KEY,
        ID_KEY,
        VERSION_KEY
    ]
}

BOOT_REGRESSIONS_VALID_KEYS = {
    "GET": [
        CREATED_KEY,
        ID_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY
    ]
}

# Used by the DistinctHandler to handle query arguments on the various
# supported resources.
DISTINCT_VALID_KEYS = {
    BOOT_COLLECTION: BOOT_VALID_KEYS,
    BUILD_COLLECTION: BUILD_VALID_KEYS,
    JOB_COLLECTION: JOB_VALID_KEYS,
    TEST_CASE_COLLECTION: TEST_CASE_VALID_KEYS,
    TEST_GROUP_COLLECTION: TEST_GROUP_VALID_KEYS
}

# Used to define, in the DistinctHandler, which fields can be used as unique.
DISTINCT_VALID_FIELDS = {
    JOB_COLLECTION: [
        COMPILER_KEY,
        COMPILER_VERSION_EXT_KEY,
        COMPILER_VERSION_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        GIT_DESCRIBE_V_KEY,
        GIT_URL_KEY,
        JOB_KEY,
        KERNEL_KEY,
        KERNEL_VERSION_KEY
    ],
    BUILD_COLLECTION: [
        ARCHITECTURE_KEY,
        COMPILER_KEY,
        BUILD_ENVIRONMENT_KEY,
        COMPILER_VERSION_EXT_KEY,
        COMPILER_VERSION_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        GIT_DESCRIBE_V_KEY,
        GIT_URL_KEY,
        JOB_KEY,
        KERNEL_KEY,
        KERNEL_VERSION_KEY
    ],
    BOOT_COLLECTION: [
        ARCHITECTURE_KEY,
        BOARD_INSTANCE_KEY,
        BOARD_KEY,
        BUILD_ENVIRONMENT_KEY,
        BOOT_JOB_URL_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        ENDIANNESS_KEY,
        GIT_BRANCH_KEY,
        GIT_COMMIT_KEY,
        GIT_DESCRIBE_KEY,
        JOB_KEY,
        KERNEL_KEY,
        LAB_NAME_KEY,
        MACH_KEY
    ],
    TEST_GROUP_COLLECTION: [
        ARCHITECTURE_KEY,
        BOARD_INSTANCE_KEY,
        BOARD_KEY,
        BOOT_ID_KEY,
        BUILD_ENVIRONMENT_KEY,
        BUILD_ID_KEY,
        DEFCONFIG_FULL_KEY,
        DEFCONFIG_KEY,
        GIT_BRANCH_KEY,
        INITRD_KEY,
        INITRD_INFO_KEY,
        IMAGE_TYPE_KEY,
        JOB_ID_KEY,
        JOB_KEY,
        KERNEL_KEY,
        LAB_NAME_KEY,
        NAME_KEY
    ],
    TEST_CASE_COLLECTION: [
        TEST_GROUP_ID_KEY,
        TEST_GROUP_NAME_KEY,
    ]
}

LAVA_CALLBACK_VALID_KEYS = {
    "POST": [
        STATUS_KEY,
        LAVA_DEFINITION_KEY,
        LAVA_DESCRIPTION_KEY,
        LAVA_START_TIME_KEY,
        LAVA_STATUS_STR_KEY,
        LAVA_RESULTS_KEY,
        LAVA_SUBMITTER_KEY,
        LAVA_ID_KEY,
        LAVA_PRIORITY_KEY,
        TOKEN_KEY,
        LAVA_END_TIME_KEY,
        LAVA_SUBMIT_TIME_KEY,
        LAVA_IS_PIPELINE_KEY,
        LAVA_METADATA_KEY,
        LAVA_FAILURE_COMMENT_KEY,
        LAVA_DEVICE_ID_KEY,
        LAVA_LOG_KEY,
    ]
}
