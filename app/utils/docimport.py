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

"""Container for all the import related functions."""

try:
    import simplejson as json
except ImportError:
    import json

import bson
import datetime
import glob
import os
import types

import models
import models.defconfig as mdefconfig
import models.job as mjob
import utils
import utils.db


def import_and_save_job(json_obj, db_options, base_path=utils.BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.

    :param json_obj: The JSON object with the values to be parsed.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return The ID of the job document created.
    """
    database = utils.db.get_db_connection(db_options)
    docs, job_id = import_job_from_json(json_obj, database, base_path)

    if docs:
        utils.LOG.info(
            "Importing %d documents with job ID: %s", len(docs), job_id)
        utils.db.save_all(database, docs, manipulate=True)
    else:
        utils.LOG.info("No jobs to save")

    return job_id


def import_job_from_json(json_obj, database, base_path=utils.BASE_PATH):
    """Import a job based on the provided JSON object.

    The provided JSON object, a dict-like object, should contain at least the
    `job` and `kernel` keys. These keys will be used to traverse the directory
    structure found at the `/job/kernel` path (starting from the default
    location).

    :param json_obj: A dict-like object, that should contain the keys `job` and
        `kernel`.
    :param base_path: The base path where to start constructing the traverse
        directory. It defaults to: /var/www/images/kernel-ci.
    :return The documents to be saved, and the job document ID.
    """
    job_dir = json_obj[models.JOB_KEY]
    kernel_dir = json_obj[models.KERNEL_KEY]

    return _import_job(job_dir, kernel_dir, database, base_path)


def _import_job(job, kernel, database, base_path=utils.BASE_PATH):
    """Traverse the job dir and create the documenst to save.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param base_path: The base path where to strat the traversing.
    :return The documents to be saved, and the job document ID.
    """
    docs = []
    ret_val = 201
    job_id = None

    job_dir = os.path.join(base_path, job)
    kernel_dir = os.path.join(job_dir, kernel)

    if utils.is_hidden(job) or utils.is_hidden(kernel):
        return docs

    job_name = (
        models.JOB_DOCUMENT_NAME %
        {models.JOB_KEY: job, models.KERNEL_KEY: kernel})

    saved_doc = utils.db.find_one(
        database[models.JOB_COLLECTION], [job_name], field=models.NAME_KEY)
    if saved_doc:
        job_doc = mjob.JobDocument.from_json(saved_doc)
        job_id = job_doc.id
    else:
        job_doc = mjob.JobDocument(job, kernel)
        ret_val, job_id = utils.db.save(database, job_doc, manipulate=True)

    if all([ret_val == 201, job_id is not None]):
        job_doc.id = job_id
        docs = _traverse_kernel_dir(job_doc, kernel_dir, database)
    else:
        utils.LOG.error("Unable to save job document %s", job_name)
        job_id = None

    return docs, job_id


def _traverse_kernel_dir(job_doc, kernel_dir, database):
    """Traverse the kernel directory looking for defconfig dirs.

    :param job_doc: The created `JobDocument`.
    :param kernel_dir: The kernel directory to traverse.
    :param database: The database connection.
    """
    docs = []

    if os.path.isdir(kernel_dir):
        if (os.path.exists(os.path.join(kernel_dir, models.DONE_FILE)) or
                glob.glob(os.path.join(kernel_dir, models.DONE_FILE_PATTERN))):
            job_doc.status = models.PASS_STATUS
        else:
            job_doc.status = models.UNKNOWN_STATUS

        if not job_doc.created_on:
            job_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)

        docs.extend(
            [
                _traverse_defconf_dir(
                    job_doc, kernel_dir, defconf_dir, database
                ) for defconf_dir in os.listdir(kernel_dir)
                if os.path.isdir(os.path.join(kernel_dir, defconf_dir))
                if not utils.is_hidden(defconf_dir)
                if not utils.is_lab_dir(defconf_dir)
                if not None
            ]
        )
    else:
        job_doc.status = models.BUILD_STATUS
        job_doc.created_on = datetime.datetime.now(tz=bson.tz_util.utc)

    # Kind of a hack:
    # We want to store some metadata at the job document level as well, like
    # git tree, git commit...
    # Since, at the moment, we do not have the metadata file at the job level
    # we need to pick one from the build documents, and extract some values.
    docs_len = len(docs)
    if docs_len > 1:
        idx = 0
        while idx < docs_len:
            defconf_doc = docs[idx]
            if isinstance(defconf_doc, mjob.JobDocument):
                idx += 1
            elif isinstance(defconf_doc, mdefconfig.DefconfigDocument):
                if (defconf_doc.job == job_doc.job and
                        defconf_doc.kernel == job_doc.kernel):
                    job_doc.git_commit = defconf_doc.git_commit
                    job_doc.git_describe = defconf_doc.git_describe
                    job_doc.git_url = defconf_doc.git_url
                    job_doc.git_branch = defconf_doc.git_branch
                    break
            else:
                idx += 1
        # Save, again, the job-doc or we end up without the git data.
        utils.db.save(database, job_doc)

    return docs


def _traverse_defconf_dir(
        job_doc, kernel_dir, defconfig_dir, database):
    """Traverse the defconfig directory looking for files.

    :param job_doc: The created `JobDocument`.
    :param kernel_dir: The parent directory of this defconfig.
    :param defconfig_dir: The actual defconfig directory to parse.
    :param database: The database connection.
    :return A `DefconfigDocument` instance.
    """
    job = job_doc.job
    kernel = job_doc.kernel
    real_dir = os.path.join(kernel_dir, defconfig_dir)

    utils.LOG.info("Traversing directory '%s'", real_dir)

    defconfig_doc = None
    for dirname, subdirs, files in os.walk(real_dir):
        # Consider only the actual directory and its files.
        subdirs[:] = []

        data_file = os.path.join(dirname, models.BUILD_META_JSON_FILE)

        if os.path.isfile(data_file):
            defconfig_doc = _parse_build_data(
                data_file, job, kernel, dirname)
            defconfig_doc.job_id = job_doc.id
            # Search for previous defconfig doc. This is only useful when
            # re-importing data and we want to have the same ID as before.
            doc_id, c_date = _search_prev_defconfig_doc(
                defconfig_doc, database)
            defconfig_doc.id = doc_id
            if c_date:
                defconfig_doc.created_on = c_date
            else:
                # Give the defconfig doc the same date as the job one.
                # In this way all defconfigs will have the same date regardless
                # of when they were saved on the file system.
                defconfig_doc.created_on = job_doc.created_on
        else:
            utils.LOG.warn("No build data file found in '%s'", real_dir)

    return defconfig_doc


def _search_prev_defconfig_doc(defconfig_doc, database):
    """Search for a similar defconfig document in the database.

    Search for an already imported defconfig/build document in the database
    and return its object ID and creation date. This is done to make sure
    we do not create double documents when re-importing the same data or
    updating it.

    :param defconfig_doc: The new defconfig document.
    :param database: The db connection.
    :return The previous doc ID and its creation date, or None.
    """
    doc_id = None
    c_date = None

    if all([defconfig_doc, database]):
        spec = {
            models.JOB_KEY: defconfig_doc.job,
            models.KERNEL_KEY: defconfig_doc.kernel,
            models.DEFCONFIG_KEY: defconfig_doc.defconfig,
            models.DEFCONFIG_FULL_KEY: defconfig_doc.defconfig_full,
            models.ARCHITECTURE_KEY: defconfig_doc.arch
        }
        prev_doc = utils.db.find(
            database[models.DEFCONFIG_COLLECTION],
            10,
            0,
            spec=spec,
            fields=[models.ID_KEY, models.CREATED_KEY]
        )

        prev_doc_count = prev_doc.count()
        if prev_doc_count > 0:
            if prev_doc_count == 1:
                doc_id = prev_doc[0].get(models.ID_KEY, None)
                c_date = prev_doc[0].get(models.CREATED_KEY, None)
            else:
                utils.LOG.warn(
                    "Found multiple defconfig docs matching: %s",
                    spec)
                utils.LOG.error(
                    "Cannot keep old document ID, don't know which one to "
                    "use!")

    return doc_id, c_date


def _parse_build_data(data_file, job, kernel, defconfig_dir):
    """Parse the metadata file contained in thie build directory.

    :param data_file: The path to the metadata file.
    :param defconf_doc: The `DefconfigDocument` whose metadata will be updated.
    """
    build_data = None
    try:
        with open(data_file) as data:
            build_data = json.load(data)
    except json.JSONDecodeError, ex:
        utils.LOG.exception(ex)
        utils.LOG.error("Error loading JSON data from '%s'", defconfig_dir)

    defconfig_doc = None

    if all([build_data, isinstance(build_data, types.DictionaryType)]):
        data_pop = build_data.pop

        try:
            defconfig = data_pop(models.DEFCONFIG_KEY)
            defconfig_full = data_pop(models.DEFCONFIG_FULL_KEY, None)
            kconfig_fragments = data_pop(models.KCONFIG_FRAGMENTS_KEY, None)

            defconfig_full = utils.get_defconfig_full(
                defconfig_dir, defconfig, defconfig_full, kconfig_fragments)

            # Err on the safe side.
            job = data_pop(models.JOB_KEY, None) or job
            kernel = data_pop(models.KERNEL_KEY, None) or kernel

            defconfig_doc = mdefconfig.DefconfigDocument(
                job, kernel, defconfig, defconfig_full)

            defconfig_doc.dirname = defconfig_dir

            defconfig_doc.arch = data_pop(models.ARCHITECTURE_KEY, None)
            defconfig_doc.build_log = data_pop(models.BUILD_LOG_KEY, None)
            defconfig_doc.build_platform = data_pop(
                models.BUILD_PLATFORM_KEY, [])
            defconfig_doc.build_time = data_pop(models.BUILD_TIME_KEY, 0)
            defconfig_doc.dtb_dir = data_pop(models.DTB_DIR_KEY, None)
            defconfig_doc.errors = data_pop(models.BUILD_ERRORS_KEY, 0)
            defconfig_doc.file_server_resource = data_pop(
                models.FILE_SERVER_RESOURCE_KEY, None)
            defconfig_doc.file_server_url = data_pop(
                models.FILE_SERVER_URL_KEY, None)
            defconfig_doc.git_branch = data_pop(models.GIT_BRANCH_KEY, None)
            defconfig_doc.git_commit = data_pop(models.GIT_COMMIT_KEY, None)
            defconfig_doc.git_describe = data_pop(
                models.GIT_DESCRIBE_KEY, None)
            defconfig_doc.git_url = data_pop(models.GIT_URL_KEY, None)
            defconfig_doc.kconfig_fragments = kconfig_fragments
            defconfig_doc.kernel_config = data_pop(
                models.KERNEL_CONFIG_KEY, None)
            defconfig_doc.kernel_image = data_pop(
                models.KERNEL_IMAGE_KEY, None)
            defconfig_doc.modules = data_pop(models.MODULES_KEY, None)
            defconfig_doc.modules_dir = data_pop(models.MODULES_DIR_KEY, None)
            defconfig_doc.status = data_pop(
                models.BUILD_RESULT_KEY, models.UNKNOWN_STATUS)
            defconfig_doc.system_map = data_pop(models.SYSTEM_MAP_KEY, None)
            defconfig_doc.text_offset = data_pop(models.TEXT_OFFSET_KEY, None)
            defconfig_doc.version = data_pop(models.VERSION_KEY, "1.0")
            defconfig_doc.warnings = data_pop(models.BUILD_WARNINGS_KEY, 0)

            defconfig_doc.metadata = build_data
        except KeyError, ex:
            utils.LOG.exception(ex)
            utils.LOG.error(
                "Missing mandatory key in build data file '%s'",
                data_file)

    return defconfig_doc
