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

"""Common bisect operations."""

import types

import models
import utils
import utils.db


BOOT_DEFCONFIG_SEARCH_FIELDS = [
    models.ARCHITECTURE_KEY,
    models.CREATED_KEY,
    models.DEFCONFIG_FULL_KEY,
    models.DEFCONFIG_KEY,
    models.GIT_BRANCH_KEY,
    models.GIT_COMMIT_KEY,
    models.GIT_DESCRIBE_KEY,
    models.GIT_URL_KEY,
    models.STATUS_KEY
]


def save_bisect_doc(database, bisect_doc, doc_id):
    """Save the provided bisect document.

    :param database: The database connection.
    :param bisect_doc: The document to save.
    :param doc_id: The ID of the document.
    """
    return_code, saved_id = utils.db.save(
        database, bisect_doc, manipulate=True)
    if return_code == 201:
        bisect_doc.id = saved_id
    else:
        utils.LOG.error("Error saving bisect data %s", doc_id)


def combine_defconfig_values(boot_doc, db_options):
    """Combine the boot document values with their own defconfing.

    It returns a dictionary whose structure is a combination
    of the values from the boot document and its associated defconfing.

    :param boot_doc: The boot document to retrieve the build of.
    :type boot_doc: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return A dictionary.
    """
    database = utils.db.get_db_connection(db_options)

    boot_doc_get = boot_doc.get

    job = boot_doc_get(models.JOB_KEY)
    kernel = boot_doc_get(models.KERNEL_KEY)
    defconfig = boot_doc_get(models.DEFCONFIG_KEY)
    defconfig_full = boot_doc_get(models.DEFCONFIG_FULL_KEY) or defconfig
    build_id = boot_doc_get(models.BUILD_ID_KEY, None)
    job_id = boot_doc_get(models.JOB_ID_KEY, None)
    arch = boot_doc_get(models.ARCHITECTURE_KEY)

    combined_values = {
        models.BISECT_BOOT_CREATED_KEY: boot_doc_get(models.CREATED_KEY),
        models.BISECT_BOOT_METADATA_KEY: boot_doc_get(models.METADATA_KEY),
        models.BISECT_BOOT_STATUS_KEY: boot_doc_get(models.STATUS_KEY),
        models.BISECT_DEFCONFIG_ARCHITECTURE_KEY: "",
        models.BISECT_DEFCONFIG_CREATED_KEY: "",
        models.BISECT_DEFCONFIG_STATUS_KEY: "",
        models.BOARD_KEY: boot_doc.get(models.BOARD_KEY, None),
        models.BOOT_ID_KEY: boot_doc_get(models.ID_KEY, None),
        models.DEFCONFIG_FULL_KEY: defconfig_full,
        models.BUILD_ID_KEY: build_id,
        models.DEFCONFIG_KEY: defconfig,
        models.DIRNAME_KEY: "",
        models.GIT_BRANCH_KEY: "",
        models.GIT_COMMIT_KEY: "",
        models.GIT_DESCRIBE_KEY: "",
        models.GIT_URL_KEY: "",
        models.JOB_ID_KEY: job_id,
        models.JOB_KEY: job,
        models.KERNEL_KEY: kernel,
        models.LAB_NAME_KEY: boot_doc_get(models.LAB_NAME_KEY, None)
    }

    if build_id:
        build_doc = utils.db.find_one2(
            database[models.BUILD_COLLECTION],
            build_id, fields=BOOT_DEFCONFIG_SEARCH_FIELDS)
    else:
        spec = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.DEFCONFIG_FULL_KEY: defconfig_full,
            models.DEFCONFIG_KEY: defconfig,
            models.ARCHITECTURE_KEY: arch
        }
        build_doc = utils.db.find_one2(
            database[models.BUILD_COLLECTION],
            spec, fields=BOOT_DEFCONFIG_SEARCH_FIELDS)

    if build_doc:
        build_doc_get = build_doc.get
        combined_values[models.DIRNAME_KEY] = build_doc_get(
            models.DIRNAME_KEY)
        combined_values[models.BISECT_DEFCONFIG_CREATED_KEY] = \
            build_doc_get(models.CREATED_KEY)
        combined_values[models.BISECT_DEFCONFIG_ARCHITECTURE_KEY] = \
            build_doc_get(models.ARCHITECTURE_KEY)
        combined_values[models.BISECT_DEFCONFIG_STATUS_KEY] = \
            build_doc_get(models.STATUS_KEY)
        combined_values[models.GIT_URL_KEY] = build_doc_get(
            models.GIT_URL_KEY, None)
        combined_values[models.GIT_BRANCH_KEY] = build_doc_get(
            models.GIT_BRANCH_KEY, None)
        combined_values[models.GIT_COMMIT_KEY] = build_doc_get(
            models.GIT_COMMIT_KEY, None)
        combined_values[models.GIT_DESCRIBE_KEY] = build_doc_get(
            models.GIT_DESCRIBE_KEY, None)

    return combined_values


def search_previous_bisect(database, spec_or_id, date_field):
    """Search for a previous saved bisect saved.

    :param database: The connection to the database.
    :param spec_or_id: The spec data structure or the ID to search for.
    :type spec_or_id: dictionary or string
    :param date_field: The name of the date field to look for in the
    `bisect_data` array as found in the database. This field is different
    between `boot` and `build` bisects.
    :type date_field: string
    :return The date of the last good commit and the number of documents.
    """
    # Search for a previous normal bisect. If we find it, use the good
    # commit date as the maximum date to search in the comparison tree
    # and retrieve at max the number of commit available in the bisect
    # data list. If we do not have the previous bisect, return max 10
    # documents since we do not know which is the last valid commit
    # we are based on.
    end_date = None
    limit = 10

    prev_bisect = utils.db.find_one2(
        database[models.BISECT_COLLECTION], spec_or_id)

    if prev_bisect:
        b_get = prev_bisect.get
        good_comit_date = b_get(models.BISECT_GOOD_COMMIT_DATE, None)
        bisect_data = b_get(models.BISECT_DATA_KEY, None)

        if good_comit_date:
            end_date = good_comit_date
        if bisect_data:
            limit = len(bisect_data)
        # If we don't have the good commit, but we have a list of
        # failed commit, pick the last one - since they are ordered by
        # creation date - and use its boot creation date.
        if not end_date and bisect_data:
            last = bisect_data[-1]
            end_date = last.get(date_field, None)

    return end_date, limit


def update_doc_fields(bisect_doc, fields):
    """Update the bisect document based on the provided fields.

    Return the dictionary view of the bisect document with the fields as
    specified in the `fields` data structure passed.

    A `fields` data structure can be a list or dictionary.

    :param bisect_doc: The document to update.
    :type bisect_doc: BisectDocument
    :param fields: A `fields` data structure with the fields to return or
    exclude. Default to None.
    :type fields: list or dict
    :return The BisectDocument as a dict calling its `to_dict()` method.
    """
    if fields:
        if isinstance(fields, list):
            bisect_doc = bisect_doc.to_dict()
            to_remove = list(bisect_doc.viewkeys() - set(fields))
            for field in to_remove:
                if field == models.ID_KEY:
                    continue
                else:
                    bisect_doc.pop(field)
        elif isinstance(fields, types.DictionaryType):
            y_fields = [
                field for field, val in fields.iteritems() if val
            ]
            n_fields = list(fields.viewkeys() - set(y_fields))

            bisect_doc = update_doc_fields(bisect_doc, y_fields)
            for field in n_fields:
                bisect_doc.pop(field, None)
        else:
            bisect_doc = bisect_doc.to_dict()
    else:
        bisect_doc = bisect_doc.to_dict()
    return bisect_doc


def get_docs_until_pass(doc_list):
    """Iterate through the docs until one that passed is found.

    Yield all documents until one that passed is found, returning it as well
    and breaking the loop.

    :param doc_list: A list of documents (`BaseDocument`) as dictionaries.
    :type doc_list: list
    """
    for doc in doc_list:
        if doc[models.STATUS_KEY] == models.PASS_STATUS:
            yield doc
            break
        yield doc
