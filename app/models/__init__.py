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
BUILD_RESULT_KEY = 'build_result'
COMPILER_VERSION_KEY = 'compiler_version'
CREATED_KEY = 'created_on'
CROSS_COMPILE_KEY = 'cross_compile'
DATE_RANGE_KEY = 'date_range'
DEFCONFIG_KEY = 'defconfig'
DIRNAME_KEY = 'dirname'
ERRORS_KEY = 'errors'
FAIL_LOG_KEY = 'fail_log'
FIELD_KEY = 'field'
GIT_BRANCH_KEY = 'git_branch'
GIT_COMMIT_KEY = 'git_commit'
GIT_DESCRIBE_KEY = 'git_describe'
GIT_URL_KEY = 'git_url'
ID_KEY = '_id'
JOB_ID_KEY = 'job_id'
JOB_KEY = 'job'
KERNEL_KEY = 'kernel'
LIMIT_KEY = 'limit'
METADATA_KEY = 'metadata'
NOT_FIELD_KEY = 'nfield'
PRIVATE_KEY = 'private'
SKIP_KEY = 'skip'
SORT_KEY = 'sort'
SORT_ORDER_KEY = 'sort_order'
STATUS_KEY = 'status'
TIME_KEY = 'time'
UPDATED_KEY = 'updated'
WARNINGS_KEY = 'warnings'

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
