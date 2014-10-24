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

"""All the bisect operations that the app can perform."""

from bson.json_util import default
from json import (
    dumps as j_dump,
    loads as j_load,
)
from pymongo import DESCENDING

from models import (
    BOOT_COLLECTION,
    DEFCONFIG_COLLECTION,
    BOARD_KEY,
    CREATED_KEY,
    DEFCONFIG_KEY,
    JOB_KEY,
    JOB_ID_KEY,
    KERNEL_KEY,
    METADATA_KEY,
    STATUS_KEY,
    ARCHITECTURE_KEY,
    DIRNAME_KEY,
    PASS_STATUS,
    BISECT_BOOT_CREATED_KEY,
    BISECT_BOOT_METADATA_KEY,
    BISECT_BOOT_STATUS_KEY,
    BISECT_DEFCONFIG_CREATED_KEY,
    BISECT_DEFCONFIG_METADATA_KEY,
    BISECT_DEFCONFIG_STATUS_KEY,
    BISECT_DEFCONFIG_ARCHITECTURE_KEY,
)
from utils.db import (
    find,
    find_one,
    get_db_connection,
)


BOOT_SEARCH_FIELDS = [
    BOARD_KEY,
    CREATED_KEY,
    DEFCONFIG_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    METADATA_KEY,
    STATUS_KEY,
]

BOOT_DEFCONFIG_SEARCH_FIELDS = [
    ARCHITECTURE_KEY,
    CREATED_KEY,
    DIRNAME_KEY,
    METADATA_KEY,
    STATUS_KEY,
]

BOOT_SORT = [(CREATED_KEY, DESCENDING)]


def _combine_defconfig_values(boot_doc, db_options):
    """Combine the boot document values with their own defconfing.

    It returns a list of dictionaries whose structure is a combination
    of the values from the boot document and its associated defconfing.

    :param boot_doc: The boot document to retrieve the defconfig of.
    :type boot_doc: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A list of dictionaries.
    """
    database = get_db_connection(db_options)

    boot_doc_get = boot_doc.get

    job = boot_doc_get(JOB_KEY)
    kernel = boot_doc_get(KERNEL_KEY)
    defconfig = boot_doc_get(DEFCONFIG_KEY)

    combined_values = {
        JOB_KEY: job,
        KERNEL_KEY: kernel,
        DEFCONFIG_KEY: defconfig,
        BISECT_BOOT_STATUS_KEY: boot_doc_get(STATUS_KEY),
        BISECT_BOOT_CREATED_KEY: boot_doc_get(CREATED_KEY),
        BISECT_BOOT_METADATA_KEY: boot_doc_get(METADATA_KEY),
        DIRNAME_KEY: "",
        BISECT_DEFCONFIG_CREATED_KEY: "",
        BISECT_DEFCONFIG_ARCHITECTURE_KEY: "",
        BISECT_DEFCONFIG_STATUS_KEY: "",
        BISECT_DEFCONFIG_METADATA_KEY: []
    }

    defconf_id = job + "-" + kernel + "-" + defconfig
    defconf_doc = find_one(
        database[DEFCONFIG_COLLECTION],
        defconf_id,
        fields=BOOT_DEFCONFIG_SEARCH_FIELDS
    )

    if defconf_doc:
        defconf_doc_get = defconf_doc.get
        combined_values[DIRNAME_KEY] = defconf_doc_get(DIRNAME_KEY)
        combined_values[BISECT_DEFCONFIG_CREATED_KEY] = defconf_doc_get(
            CREATED_KEY
        )
        combined_values[BISECT_DEFCONFIG_ARCHITECTURE_KEY] = defconf_doc_get(
            ARCHITECTURE_KEY
        )
        combined_values[BISECT_DEFCONFIG_STATUS_KEY] = defconf_doc_get(
            STATUS_KEY
        )
        combined_values[BISECT_DEFCONFIG_METADATA_KEY] = defconf_doc_get(
            METADATA_KEY
        )

    return combined_values


def execute_boot_bisection(doc_id, db_options):
    """Perform a bisect-like on the provided boot report.

    It searches all the previous boot reports starting from the provided one
    until it finds one whose boot passed. After that, it looks for all the
    defconfig reports and combines the value into a single data structure.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A numeric value for the result status and a list dictionaries.
    """
    database = get_db_connection(db_options)

    start_doc = find_one(
        database[BOOT_COLLECTION], doc_id, fields=BOOT_SEARCH_FIELDS
    )

    result = []
    code = 200

    if start_doc:
        start_doc_get = start_doc.get
        spec = {
            BOARD_KEY: start_doc_get(BOARD_KEY),
            DEFCONFIG_KEY: start_doc_get(DEFCONFIG_KEY),
            JOB_KEY: start_doc_get(JOB_KEY),
            CREATED_KEY: {
                "$lt": start_doc_get(CREATED_KEY)
            }
        }

        all_valid_docs = [(start_doc, db_options)]

        all_prev_docs = find(
            database[BOOT_COLLECTION],
            0,
            0,
            spec=spec,
            fields=BOOT_SEARCH_FIELDS,
            sort=BOOT_SORT
        )

        if all_prev_docs:
            for prev_doc in all_prev_docs:
                if prev_doc[STATUS_KEY] == PASS_STATUS:
                    all_valid_docs.append((prev_doc, db_options))
                    break
                all_valid_docs.append((prev_doc, db_options))

        func = _combine_defconfig_values
        # TODO: we have to save the result in a new collection.
        result = [
            j_load(j_dump(func(doc, opt), default=default))
            for doc, opt in all_valid_docs
        ]
    else:
        code = 404
        result = None

    return code, result
