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

"""Convert the defconfig_id fields into the new build_id one."""

import multiprocessing

import models
import utils
import utils.db


database = utils.db.get_db_connection({})


def add_build_type_field(collection_name):
    utils.LOG.info("Updating build collection")
    collection = database[collection_name]

    for doc in collection.find():
        ret_val = utils.db.update2(
            collection,
            {models.ID_KEY: doc[models.ID_KEY]},
            {"$set": {models.BUILD_TYPE_KEY: models.KERNEL_BUILD_TYPE}}
        )

        if ret_val == 500:
            utils.LOG.error(
                "Error updating build document %s", str(doc[models.ID_KEY]))


def convert_defconfig_id(collection_name):
    utils.LOG.info("Converting collection %s", collection_name)

    collection = database[collection_name]
    update_doc = {
        "$set": None,
        "$unset": {"defconfig_id": ""}
    }

    for doc in collection.find():
        update_doc["$set"] = {
            models.BUILD_ID_KEY: doc.get("defconfig_id", None)
        }

        ret_val = utils.db.update2(
            collection, {models.ID_KEY: doc[models.ID_KEY]}, update_doc)

        if ret_val == 500:
            utils.LOG.error(
                "Error updating document %s", str(doc[models.ID_KEY]))


if __name__ == "__main__":
    process_pool = multiprocessing.Pool(4)
    process_pool.map(
        convert_defconfig_id,
        [
            models.BOOT_COLLECTION,
            models.TEST_GROUP_COLLECTION,
            models.ERROR_LOGS_COLLECTION
        ]
    )
    process_pool.apply(add_build_type_field, (models.BUILD_COLLECTION,))

    process_pool.close()
    process_pool.join()
