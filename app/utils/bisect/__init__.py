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

from bson import tz_util
from bson.json_util import default
from datetime import datetime
from json import (
    dumps as j_dump,
    loads as j_load,
)
from pymongo import DESCENDING
from types import DictionaryType

from models import (
    ARCHITECTURE_KEY,
    BISECT_BOOT_CREATED_KEY,
    BISECT_BOOT_METADATA_KEY,
    BISECT_BOOT_STATUS_KEY,
    BISECT_DEFCONFIG_ARCHITECTURE_KEY,
    BISECT_DEFCONFIG_CREATED_KEY,
    BISECT_DEFCONFIG_METADATA_KEY,
    BISECT_DEFCONFIG_STATUS_KEY,
    BOARD_KEY,
    BOOT_COLLECTION,
    CREATED_KEY,
    DEFCONFIG_COLLECTION,
    DEFCONFIG_KEY,
    DIRNAME_KEY,
    GIT_COMMIT_KEY,
    GIT_URL_KEY,
    ID_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    METADATA_KEY,
    PASS_STATUS,
    STATUS_KEY,
)
from models.bisect import BootBisectDocument
from utils import LOG
from utils.db import (
    find,
    find_one,
    get_db_connection,
    save,
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
        BISECT_DEFCONFIG_METADATA_KEY: {}
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


def execute_boot_bisection(doc_id, db_options, fields=None):
    """Perform a bisect-like on the provided boot report.

    It searches all the previous boot reports starting from the provided one
    until it finds one whose boot passed. After that, it looks for all the
    defconfig reports and combines the value into a single data structure.

    :param doc_id: The boot document ID.
    :type doc_id: str
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return A numeric value for the result status and a list dictionaries.
    """
    database = get_db_connection(db_options)
    result = []
    code = 200

    start_doc = find_one(
        database[BOOT_COLLECTION], doc_id, fields=BOOT_SEARCH_FIELDS
    )

    if all([start_doc, isinstance(start_doc, DictionaryType)]):
        start_doc_get = start_doc.get

        if start_doc_get(STATUS_KEY) == PASS_STATUS:
            code = 400
            result = None
        else:
            bisect_doc = BootBisectDocument(doc_id)
            bisect_doc.job = start_doc_get(JOB_ID_KEY)
            bisect_doc.created_on = datetime.now(tz=tz_util.utc)
            bisect_doc.board = start_doc_get(BOARD_KEY)

            spec = {
                BOARD_KEY: start_doc_get(BOARD_KEY),
                DEFCONFIG_KEY: start_doc_get(DEFCONFIG_KEY),
                JOB_KEY: start_doc_get(JOB_KEY),
                CREATED_KEY: {
                    "$lt": start_doc_get(CREATED_KEY)
                }
            }

            # The function to apply to each boot document to find its defconfig
            # one and combine the values.
            func = _combine_defconfig_values

            bad_doc = func(start_doc, db_options)
            bad_doc_meta = bad_doc[BISECT_DEFCONFIG_METADATA_KEY].get

            bisect_doc.bad_commit_date = bad_doc[BISECT_DEFCONFIG_CREATED_KEY]
            bisect_doc.bad_commit = bad_doc_meta(GIT_COMMIT_KEY)
            bisect_doc.bad_commit_url = bad_doc_meta(GIT_URL_KEY)

            all_valid_docs = [bad_doc]

            # Search through all the previous boot reports, until one that
            # passed is found, and combine them with their defconfig document.
            all_prev_docs = find(
                database[BOOT_COLLECTION],
                0,
                0,
                spec=spec,
                fields=BOOT_SEARCH_FIELDS,
                sort=BOOT_SORT
            )

            if all_prev_docs:
                all_valid_docs.extend(
                    [
                        func(doc, db_options)
                        for doc in _get_docs_until_pass(all_prev_docs)
                    ]
                )
                # The last doc should be the good one, in case it is, add the
                # values to the bisect_doc.
                good_doc = all_valid_docs[-1]
                if good_doc[BISECT_BOOT_STATUS_KEY] == PASS_STATUS:
                    good_doc_meta = good_doc[BISECT_DEFCONFIG_METADATA_KEY].get
                    bisect_doc.good_commit = good_doc_meta(GIT_COMMIT_KEY)
                    bisect_doc.good_commit_url = good_doc_meta(GIT_URL_KEY)
                    bisect_doc.good_commit_date = \
                        good_doc[BISECT_DEFCONFIG_CREATED_KEY]

            # Store everything in the bisect_data list of the bisect_doc.
            bisect_doc.bisect_data = all_valid_docs

            return_code, saved_id = save(database, bisect_doc, manipulate=True)
            if return_code == 201:
                bisect_doc.id = saved_id
            else:
                LOG.error("Error savind bisect data %s", doc_id)

            bisect_doc = _update_doc_fields(bisect_doc, fields)
            result = [j_load(j_dump(bisect_doc, default=default))]
    else:
        code = 404
        result = None

    return code, result


def _update_doc_fields(bisect_doc, fields):
    """Update the bisect document based on the provided fields.

    Return the dictionary view of the bisect document with the fields as
    specified in the `fields` data structure passed.

    A `fields` data structure can be a list or dictionary.

    :param bisect_doc: The document to update.
    :type bisect_doc: BisectDocument
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The BisectDocument as a dictionary.
    """
    if fields:
        if isinstance(fields, list):
            bisect_doc = bisect_doc.to_dict()
            to_remove = list(bisect_doc.viewkeys() - set(fields))
            for field in to_remove:
                if field == ID_KEY:
                    continue
                else:
                    bisect_doc.pop(field)
        elif isinstance(fields, DictionaryType):
            y_fields = [
                field for field, val in fields.iteritems() if val
            ]
            n_fields = list(fields.viewkeys() - set(y_fields))

            bisect_doc = _update_doc_fields(bisect_doc, y_fields)
            for field in n_fields:
                bisect_doc.pop(field, None)
        else:
            bisect_doc = bisect_doc.to_dict()
    else:
        bisect_doc = bisect_doc.to_dict()
    return bisect_doc


def _get_docs_until_pass(doc_list):
    """Iterate through the docs until one that passed is found.

    Yield all documents until one that passed is found, returning it as well
    and breaking the loop.

    :param doc_list: A list of documents (`BaseDocument`) as dictionaries.
    :type doc_list: list
    """
    for doc in doc_list:
        if doc[STATUS_KEY] == PASS_STATUS:
            yield doc
            break
        yield doc
