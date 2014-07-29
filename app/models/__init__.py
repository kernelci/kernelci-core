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

# The default mongodb database name.
DB_NAME = 'kernel-ci'

# The default ID key, and other keys, for mongodb documents and queries.
AGGREGATE_KEY = 'aggregate'
ARCHITECTURE_KEY = 'arch'
BOARD_KEY = 'board'
BOOT_LOG_KEY = 'boot_log'
BUILD_RESULT_KEY = 'build_result'
COMPILER_VERSION_KEY = 'compiler_version'
CREATED_KEY = 'created_on'
CROSS_COMPILE_KEY = 'cross_compile'
DATE_RANGE_KEY = 'date_range'
DEFCONFIG_KEY = 'defconfig'
DIRNAME_KEY = 'dirname'
DTB_ADDR_KEY = 'dtb_addr'
DTB_KEY = 'dtb'
EMAIL_KEY = 'email'
ENDIANNESS_KEY = 'endian'
ERRORS_KEY = 'errors'
EXPIRED_KEY = 'expired'
EXPIRES_KEY = 'expires_on'
FIELD_KEY = 'field'
GIT_BRANCH_KEY = 'git_branch'
GIT_COMMIT_KEY = 'git_commit'
GIT_DESCRIBE_KEY = 'git_describe'
GIT_URL_KEY = 'git_url'
ID_KEY = '_id'
INITRD_ADDR_KEY = 'initrd_addr'
IP_ADDRESS_KEY = 'ip_address'
JOB_ID_KEY = 'job_id'
JOB_KEY = 'job'
KERNEL_IMAGE_KEY = 'kernel_image'
KERNEL_KEY = 'kernel'
LIMIT_KEY = 'limit'
LOAD_ADDR_KEY = 'load_addr'
METADATA_KEY = 'metadata'
NOT_FIELD_KEY = 'nfield'
PRIVATE_KEY = 'private'
PROPERTIES_KEY = 'properties'
SKIP_KEY = 'skip'
SORT_KEY = 'sort'
SORT_ORDER_KEY = 'sort_order'
STATUS_KEY = 'status'
TIME_KEY = 'time'
TOKEN_KEY = 'token'
UPDATED_KEY = 'updated'
USERNAME_KEY = 'username'
WARNINGS_KEY = 'warnings'

# Token special fields.
ADMIN_KEY = 'admin'
DELETE_KEY = 'delete'
GET_KEY = 'get'
IP_RESTRICTED = 'ip_restricted'
POST_KEY = 'post'
SUPERUSER_KEY = 'superuser'

# Job and/or build status.
BUILD_STATUS = 'BUILD'
FAIL_STATUS = 'FAIL'
PASS_STATUS = 'PASS'
UNKNOWN_STATUS = 'UNKNOWN'

# Build file names.
DONE_FILE = '.done'
BUILD_META_FILE = 'build.meta'
BUILD_META_JSON_FILE = 'build.json'
BUILD_FAIL_FILE = 'build.FAIL'
BUILD_PASS_FILE = 'build.PASS'
