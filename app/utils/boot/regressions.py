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

"""Logic to find regressions in boot reports."""

import bson
import redis

import models
import utils
import utils.database.redisdb as redisdb
import utils.db

# How the key to access the regressions data structure is formatted.
# Done in this way so that we can use mongodb dot notation to access embedded
# documents.
REGRESSION_FMT = "{:s}.{:s}.{:s}.{:s}.{:s}.{:s}"
# The real data structure is accessed with the name of the key followed by
# the rest of the embedded document key.
REGRESSION_DOT_FMT = "{:s}.{:s}"
# Lock key format for the Redis lock.
LOCK_KEY_FMT = "boot-regressions-{:s}-{:s}"


def get_regressions_by_key(key, regressions):
    """From a formatted key, get the actual regressions list.

    :param key: The key we need to look up.
    :type key: str
    :param regressions: The regressions data structure.
    :type regressions: dict
    :return list The regressions for the passed key.
    """
    k = key.split(".")
    regr = []
    try:
        regr = regressions[k[0]][k[1]][k[2]][k[3]][k[4]][k[5]]
    except (IndexError, KeyError):
        utils.LOG.error("Error retrieving regressions with key: %s", key)

    return regr


def sanitize_key(key):
    """Remove and replace invalid characters from a key.

    MongoDB's document keys must not contain some special characters.

    :param key: The key to sanitize.
    :type key: str
    :return str The sanitized key.
    """
    sanitized = key
    if key:
        sanitized = key.replace(" ", "").replace(".", ":")

    return sanitized


def gen_regression_keys(regressions):
    """Go through the regression data structure and yield the "keys".

    The regression data structure is a dictionary with nested dictionaries.

    :param regressions: The data structure that contains the regressions.
    :type regressions: dict
    :return str The regression key.
    """
    for lab in regressions.viewkeys():
        lab_d = regressions[lab]

        for arch in lab_d.viewkeys():
            arch_d = lab_d[arch]

            for board in arch_d.viewkeys():
                board_d = arch_d[board]

                for b_instance in board_d.viewkeys():
                    instance_d = board_d[b_instance]

                    for defconfig in instance_d.viewkeys():
                        defconfig_d = instance_d[defconfig]

                        for compiler in defconfig_d.viewkeys():
                            yield REGRESSION_FMT.format(
                                lab,
                                arch,
                                board, b_instance, defconfig, compiler
                            )


def check_prev_regression(job, kernel, job_id, conn):
    """Look up a previous regression document.

    :param job: The job value.
    :type job: str
    :param kernel: The kernel value.
    :type kernel: str
    :param job_id: The ID of the job.
    :type job_id: bson.objectid.ObjectId
    :param conn: The database connection.
    :return The database query result.
    """
    spec = {models.JOB_KEY: job, models.KERNEL_KEY: kernel}
    if job_id:
        spec[models.JOB_ID_KEY] = job_id

    return utils.db.find_one2(conn[models.BOOT_REGRESSIONS_COLLECTION], spec)


# pylint: disable=too-many-locals
def track_regression(boot_doc, pass_doc, old_regr_doc, conn, db_options):
    """Track the regression for the provided boot report.

    :param boot_doc: The actual boot document where we have a regression.
    :type boot_doc: dict
    :param pass_doc: The previous boot document, when we start tracking a
    regression.
    :type pass_doc: dict
    :param old_regr_doc: The previous regressions document.
    :type old_regr_doc: dict
    :param conn: The database connection.
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return tuple The status code (200, 201, 500); and the regression
    document id.
    """
    ret_val = 201
    doc_id = None

    b_get = boot_doc.get
    arch = b_get(models.ARCHITECTURE_KEY)
    b_instance = sanitize_key(str(b_get(models.BOARD_INSTANCE_KEY)).lower())
    board = sanitize_key(b_get(models.BOARD_KEY))
    compiler = sanitize_key(str(b_get(models.COMPILER_VERSION_EXT_KEY)))
    defconfig = sanitize_key(b_get(models.DEFCONFIG_FULL_KEY))
    job = b_get(models.JOB_KEY)
    job_id = b_get(models.JOB_ID_KEY)
    kernel = b_get(models.KERNEL_KEY)
    lab = b_get(models.LAB_NAME_KEY)

    regr_key = REGRESSION_FMT.format(
        lab, arch, board, b_instance, defconfig, compiler)

    # Do we have "old" regressions?
    regr_docs = []
    if old_regr_doc:
        old_regr = old_regr_doc[models.REGRESSIONS_KEY]
        if regr_key in gen_regression_keys(old_regr):
            regr_docs = get_regressions_by_key(regr_key, old_regr)

    if pass_doc:
        regr_docs.append(pass_doc)

    regr_docs.append(boot_doc)

    # We might be importing boot in parallel through multi-processes.
    # Keep a lock here when looking for the previous regressions or we might
    # end up with multiple boot regression creations.
    redis_conn = redisdb.get_db_connection(db_options)
    lock_key = LOCK_KEY_FMT.format(job, kernel)

    with redis.lock.Lock(redis_conn, lock_key, timeout=5):
        # Do we have already a regression registered for this job_id,
        # job, kernel?
        prev_reg_doc = check_prev_regression(job, kernel, job_id, conn)
        if prev_reg_doc:
            doc_id = prev_reg_doc[models.ID_KEY]
            prev_regs = prev_reg_doc[models.REGRESSIONS_KEY]

            regr_data_key = \
                REGRESSION_DOT_FMT.format(models.REGRESSIONS_KEY, regr_key)

            if regr_key in gen_regression_keys(prev_regs):
                # If we also have the same key in the document, append the
                # new boot report.
                document = {"$addToSet": {regr_data_key: boot_doc}}
            else:
                # Otherwise just set the new key.
                document = {"$set": {regr_data_key: regr_docs}}

            ret_val = utils.db.update2(
                conn,
                models.BOOT_REGRESSIONS_COLLECTION,
                {models.ID_KEY: prev_reg_doc[models.ID_KEY]},
                document
            )
        else:
            regression_doc = {
                models.JOB_KEY: job,
                models.KERNEL_KEY: kernel,
                models.JOB_ID_KEY: job_id
            }

            # The regression data structure.
            # A dictionary with nested keys, whose keys in nested order are:
            # lab name
            # architecture type
            # board name
            # board instance or the string "none"
            # defconfig full string
            # compiler string (just compiler + version)
            # The regressions are stored in a list as the value of the
            # "compiler" key.
            regression_doc[models.REGRESSIONS_KEY] = {
                lab: {
                    arch: {
                        board: {
                            b_instance: {
                                defconfig: {
                                    compiler: regr_docs
                                }
                            }
                        }
                    }
                }
            }

            ret_val, doc_id = \
                utils.db.save2(
                    conn, models.BOOT_REGRESSIONS_COLLECTION, regression_doc)

    return ret_val, doc_id


def check_and_track(boot_doc, conn, db_options):
    """Check previous boot report and start tracking regressions.

    :param boot_doc: The boot document we are working on.
    :type boot_doc: dict
    :param conn: The database connection.
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return tuple The return value; and the regression document id.
    """
    ret_val = None
    doc_id = None

    b_get = boot_doc.get
    # Look for an older and as much similar as possible boot report.
    # In case the boot report we are analyzing is FAIL and the old one is PASS
    # it's a new regression that we need to track.
    old_doc = utils.db.find_one2(
        conn[models.BOOT_COLLECTION],
        {
            models.ARCHITECTURE_KEY: b_get(models.ARCHITECTURE_KEY),
            models.BOARD_INSTANCE_KEY: b_get(models.BOARD_INSTANCE_KEY),
            models.BOARD_KEY: b_get(models.BOARD_KEY),
            models.COMPILER_VERSION_EXT_KEY:
                b_get(models.COMPILER_VERSION_EXT_KEY),
            models.CREATED_KEY: {"$lt": b_get(models.CREATED_KEY)},
            models.DEFCONFIG_FULL_KEY: b_get(models.DEFCONFIG_FULL_KEY),
            models.DEFCONFIG_KEY: b_get(models.DEFCONFIG_KEY),
            models.JOB_KEY: b_get(models.JOB_KEY),
            models.LAB_NAME_KEY: b_get(models.LAB_NAME_KEY)
        }
    )

    if old_doc:
        old_status = old_doc[models.STATUS_KEY]

        if old_status == "FAIL":
            # "Old" regression case, we might have to keep track of it.
            utils.LOG.info("Found previous failed boot report")
            # Check if we have old regressions first.
            # If not, we don't track it since it's the first time we
            # know about it.
            prev_reg = \
                check_prev_regression(
                    old_doc[models.JOB_KEY],
                    old_doc[models.KERNEL_KEY],
                    old_doc[models.JOB_ID_KEY], conn)
            if prev_reg:
                utils.LOG.info("Found previous regressions, tracking")
                ret_val, doc_id = track_regression(
                    boot_doc, None, prev_reg, conn, db_options)
            else:
                utils.LOG.info(
                    "No previous regressions found, not tracking")
        elif old_status == "PASS":
            # New regression case.
            utils.LOG.info("Found previous passed boot report, tracking")
            ret_val, doc_id = track_regression(
                boot_doc, old_doc, None, conn, db_options)
    else:
        utils.LOG.info("No previous boot report found, not tracking")

    return ret_val, doc_id


def find(boot_id, db_options):
    """Find the regression starting from a single boot report.

    :param boot_id: The id of the boot document. Must be a valid ObjectId.
    :type boot_id: str, ObjectId
    :param db_options: The database connection parameters.
    :type db_options: dict
    :return tuple The return value that can be 200, 201 or 500; the Id of the
    regression document or None.
    """
    results = (None, None)
    conn = None

    try:
        conn = utils.db.get_db_connection(db_options)

        if not isinstance(boot_id, bson.objectid.ObjectId):
            try:
                boot_id = bson.objectid.ObjectId(boot_id)
            except bson.errors.InvalidId:
                boot_id = None
                utils.LOG.error("Error converting boot id '%s'", str(boot_id))

        if boot_id:
            boot_doc = utils.db.find_one2(
                conn[models.BOOT_COLLECTION], {models.ID_KEY: boot_id})

            if boot_doc and boot_doc[models.STATUS_KEY] == "FAIL":
                utils.LOG.info(
                    "Searching regressions for boot '%s'", str(boot_id))
                results = check_and_track(boot_doc, conn, db_options)
    finally:
        if conn:
            conn.connection.close()

    return results
