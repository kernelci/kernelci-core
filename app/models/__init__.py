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
ID_KEY = '_id'
CREATED_KEY = 'created_on'
DATE_RANGE_KEY = 'date_range'
SKIP_KEY = 'skip'
LIMIT_KEY = 'limit'
SORT_ORDER_KEY = 'sort_order'
SORT_KEY = 'sort'
FIELD_KEY = 'field'
NOT_FIELD_KEY = 'nfield'
AGGREGATE_KEY = 'aggregate'
DEFCONFIG_KEY = 'defconfig'
BUILD_RESULT_KEY = 'build_result'
WARNINGS_KEY = 'warnings'
ERRORS_KEY = 'errors'
ARCHITECTURE_KEY = 'arch'
JOB_KEY = 'job'
KERNEL_KEY = 'kernel'

# Job and/or build status.
BUILD_STATUS = 'BUILD'
FAIL_STATUS = 'FAIL'
PASS_STATUS = 'PASS'
UNKNOWN_STATUS = 'UNKNOWN'

# Build file names.
DONE_FILE = '.done'
BUILD_META_FILE = 'build.meta'
BUILD_FAIL_FILE = 'build.FAIL'
BUILD_PASS_FILE = 'build.PASS'
