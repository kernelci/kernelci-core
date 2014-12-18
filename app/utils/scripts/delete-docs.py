#!/usr/bin/python
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

"""Basic command line script to delete documents."""

import argparse
import sys

import handlers.common
import models
import utils
import utils.db


COLLECTIONS = [
    models.BOOT_COLLECTION,
    models.DEFCONFIG_COLLECTION,
    models.JOB_COLLECTION,
    models.LAB_COLLECTION
]

ALL_COLLECTIONS = [
    "all"
]
ALL_COLLECTIONS.extend(COLLECTIONS)


def parse_fields(fields):
    for field in fields:
        if "=" in field:
            yield field.split("=", 1)
        else:
            utils.LOG.error("Field %s is not valid, not considered", field)


def _delete_with_spec(collection, spec_or_id, database):
    ret_val = None
    if collection == "all":
        utils.LOG.info("Deleting documents in all collections")
        for coll in COLLECTIONS:
            utils.LOG.info("Deleting from %s...", coll)
            ret_val = utils.db.delete(database[coll], spec)
    else:
        ret_val = utils.db.delete(database[collection], spec_or_id)

    if ret_val == 200:
        utils.LOG.info("Documents identified deleted: %s", spec_or_id)
    else:
        utils.LOG.error(
            "Error deleting documents with the provided values: %s",
            spec_or_id)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import boots from disk",
        version=0.1
    )
    parser.add_argument(
        "--collection", "-c",
        type=str,
        help="The name of the job to import",
        dest="collection",
        required=True,
        choices=ALL_COLLECTIONS
    )
    parser.add_argument(
        "--field", "-f",
        help=(
            "The necessary fields to identify the elements to delete; "
            "they must be defined as key=value pairs"
        ),
        dest="fields",
        action="append",
        required=True
    )

    args = parser.parse_args()

    collection = args.collection
    fields = args.fields

    spec = {
        k: v for k, v in parse_fields(fields)
    }
    handlers.common.update_id_fields(spec)

    if spec:
        database = utils.db.get_db_connection({})
        _delete_with_spec(collection, spec, database)
    else:
        utils.LOG.error("Don't know what to look for...")
        sys.exit(1)
