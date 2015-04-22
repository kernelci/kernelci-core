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
ARM64_ARCHITECTURE_KEY = "arm64"
ARM_ARCHITECTURE_KEY = "arm"
ATTACHMENTS_KEY = "attachments"
BOARD_INSTANCE_KEY = "board_instance"
BOARD_KEY = "board"
BOOT_ID_KEY = "boot_id"
BOOT_LOAD_ADDR_KEY = "loadaddr"
BOOT_LOG_HTML_KEY = "boot_log_html"
BOOT_LOG_KEY = "boot_log"
BOOT_RESULT_DESC_KEY = "boot_result_description"
BOOT_RESULT_KEY = "boot_result"
BOOT_RETRIES_KEY = "boot_retries"
BOOT_TIME_KEY = "boot_time"
BOOT_WARNINGS_KEY = "boot_warnings"
BUILD_ERRORS_KEY = "build_errors"
BUILD_LOG_KEY = "build_log"
BUILD_PLATFORM_KEY = "build_platform"
BUILD_RESULT_KEY = "build_result"
BUILD_TIME_KEY = "build_time"
BUILD_WARNINGS_KEY = "build_warnings"
COMPARED_KEY = "compared"
COMPARE_TO_KEY = "compare_to"
COMPILER_VERSION_KEY = "compiler_version"
CONTACT_KEY = "contact"
COUNT_KEY = "count"
CREATED_KEY = "created_on"
CROSS_COMPILE_KEY = "cross_compile"
DATE_RANGE_KEY = "date_range"
DEFCONFIG_FULL_KEY = "defconfig_full"
DEFCONFIG_ID_KEY = "defconfig_id"
DEFCONFIG_KEY = "defconfig"
DEFINITION_URI_KEY = "definition_uri"
DIRNAME_KEY = "dirname"
DOC_ID_KEY = "doc_id"
DTB_ADDR_KEY = "dtb_addr"
DTB_APPEND_KEY = "dtb_append"
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
FILE_SERVER_RESOURCE_KEY = "file_server_resource"
FILE_SERVER_URL_KEY = "file_server_url"
GIT_BRANCH_KEY = "git_branch"
GIT_COMMIT_KEY = "git_commit"
GIT_DESCRIBE_KEY = "git_describe"
GIT_URL_KEY = "git_url"
GTE_KEY = "gte"
ID_KEY = "_id"
INITRD_ADDR_KEY = "initrd_addr"
INITRD_KEY = "initrd"
IP_ADDRESS_KEY = "ip_address"
JOB_ID_KEY = "job_id"
JOB_KEY = "job"
KCONFIG_FRAGMENTS_KEY = "kconfig_fragments"
KERNEL_CONFIG_KEY = "kernel_config"
KERNEL_IMAGE_KEY = "kernel_image"
KERNEL_KEY = "kernel"
KVM_GUEST_KEY = "kvm_guest"
LAB_ID_KEY = "lab_id"
LAB_NAME_KEY = "lab_name"
LIMIT_KEY = "limit"
LOAD_ADDR_KEY = "load_addr"
LT_KEY = "lt"
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
NAME_KEY = "name"
NOT_FIELD_KEY = "nfield"
PARAMETERS_KEY = "parameters"
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
STATUS_KEY = "status"
SURNAME_KEY = "surname"
SYSTEM_MAP_KEY = "system_map"
TEST_CASE_ID_KEY = "test_case_id"
TEST_CASE_KEY = "test_case"
TEST_SET_ID_KEY = "test_set_id"
TEST_SET_KEY = "test_set"
TEST_SUITE_ID_KEY = "test_suite_id"
TEXT_OFFSET_KEY = "text_offset"
TIME_KEY = "time"
TOKEN_KEY = "token"
TYPE_KEY = "type"
UIMAGE_ADDR_KEY = "uimage_addr"
UIMAGE_KEY = "uimage"
UPDATED_KEY = "updated_on"
USERNAME_KEY = "username"
VCS_COMMIT_KEY = "vcs_commit"
VERSION_FULL_KEY = "full_version"
VERSION_KEY = "version"
WARNINGS_COUNT_KEY = "warnings_count"
WARNINGS_KEY = "warnings"
x86_ARCHITECTURE_KEY = "x86"

# Email reporting control fields.
SEND_BOOT_REPORT_KEY = "boot_report"
SEND_BUILD_REPORT_KEY = "build_report"
BOOT_REPORT_SEND_TO_KEY = "boot_send_to"
BUILD_REPORT_SEND_TO_KEY = "build_send_to"
REPORT_SEND_TO_KEY = "send_to"
DELAY_KEY = "delay"

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
DOCUMENT_ID_KEY = "document_id"
QUERY_KEY = "query"
OP_ID_KEY = "operation_id"

# Collection names.
BOOT_COLLECTION = "boot"
COUNT_COLLECTION = "count"
DEFCONFIG_COLLECTION = "defconfig"
JOB_COLLECTION = "job"
SUBSCRIPTION_COLLECTION = "subscription"
TOKEN_COLLECTION = "api-token"
BISECT_COLLECTION = "bisect"
LAB_COLLECTION = "lab"
REPORT_COLLECTION = "report"
UPLOAD_COLLECTION = "upload"
TEST_SUITE_COLLECTION = "test_suite"
TEST_CASE_COLLECTION = "test_case"
TEST_SET_COLLECTION = "test_set"
ERROR_LOGS_COLLECTION = "error_logs"
ERRORS_SUMMARY_COLLECTION = "errors_summary"

# Report types.
BUILD_REPORT = "build"
BOOT_REPORT = "boot"

# Bisect values.
BISECT_BOOT_STATUS_KEY = "boot_status"
BISECT_BOOT_CREATED_KEY = "boot_created_on"
BISECT_BOOT_METADATA_KEY = "boot_metadata"
BISECT_DEFCONFIG_STATUS_KEY = "defconfig_status"
BISECT_DEFCONFIG_CREATED_KEY = "defconfig_created_on"
BISECT_DEFCONFIG_METADATA_KEY = "defconfig_metadata"
BISECT_DEFCONFIG_ARCHITECTURE_KEY = "defconfig_arch"
BISECT_DATA_KEY = "bisect_data"
BISECT_GOOD_COMMIT_KEY = "good_commit"
BISECT_BAD_COMMIT_KEY = "bad_commit"
BISECT_GOOD_COMMIT_DATE = "good_commit_date"
BISECT_BAD_COMMIT_DATE = "bad_commit_date"
BISECT_GOOD_COMMIT_URL = "good_commit_url"
BISECT_BAD_COMMIT_URL = "bad_commit_url"

VALID_ARCHITECTURES = [
    ARM64_ARCHITECTURE_KEY,
    ARM_ARCHITECTURE_KEY,
    x86_ARCHITECTURE_KEY
]

# Name formats.
JOB_DOCUMENT_NAME = "%(job)s-%(kernel)s"
BOOT_DOCUMENT_NAME = "%(board)s-%(job)s-%(kernel)s-%(defconfig)s-%(arch)s"
DEFCONFIG_DOCUMENT_NAME = "%(job)s-%(kernel)s-%(defconfig)s"
SUBSCRIPTION_DOCUMENT_NAME = "sub-%(job)s-%(kernel)s"

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
    UNTRIED_STATUS,
]

# Valid job status.
VALID_JOB_STATUS = [
    BUILD_STATUS,
    FAIL_STATUS,
    PASS_STATUS,
    UNKNOWN_STATUS,
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
    DEFCONFIG_COLLECTION,
]

VALID_EMAIL_FORMATS = [
    EMAIL_HTML_FORMAT_KEY,
    EMAIL_TXT_FORMAT_KEY
]
