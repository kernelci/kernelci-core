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

"""Container for all the import related functions."""

import glob
import os
import pymongo

from bson import tz_util
from datetime import datetime

import models
import models.defconfig as moddf
import models.job as modj
import utils
import utils.db
import utils.meta_parser


def import_and_save_job(json_obj, db_options, base_path=utils.BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.

    :param json_obj: The JSON object with the values to be parsed.
    :type json_obj: dict
    :param db_options: The mongodb database connection parameters.
    :type db_options: dict
    :return The ID of the created document.
    """
    database = utils.db.get_db_connection(db_options)
    docs, job_id = import_job_from_json(json_obj, database, base_path)

    if docs:
        utils.LOG.info(
            "Importing %d documents with job ID: %s", len(docs), job_id
        )
        utils.db.save(database, docs)
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
    job_dir = os.path.join(base_path, job)
    kernel_dir = os.path.join(job_dir, kernel)

    if utils.is_hidden(job) or utils.is_hidden(kernel):
        return docs

    job_name = (
        models.JOB_DOCUMENT_NAME %
        {models.JOB_KEY: job, models.KERNEL_KEY: kernel}
    )

    saved_doc = utils.db.find_one(
        database[models.JOB_COLLECTION], [job_name], field="name"
    )
    if saved_doc:
        job_doc = modj.JobDocument.from_json(saved_doc)
    else:
        job_doc = modj.JobDocument(job, kernel)

    docs.append(job_doc)

    if os.path.isdir(kernel_dir):
        if (os.path.exists(os.path.join(kernel_dir, models.DONE_FILE)) or
                glob.glob(os.path.join(kernel_dir, models.DONE_FILE_PATTERN))):
            job_doc.status = models.PASS_STATUS
        else:
            job_doc.status = models.UNKNOWN_STATUS

        # If the job dir exists, read the last modification time from the
        # file system and use that as the creation date.
        if not job_doc.created_on:
            job_doc.created_on = datetime.fromtimestamp(
                os.stat(kernel_dir).st_mtime, tz=tz_util.utc)

        docs.extend(
            [
                _traverse_defconf_dir(
                    job, kernel, kernel_dir, defconf_dir
                ) for defconf_dir in os.listdir(kernel_dir)
                if os.path.isdir(os.path.join(kernel_dir, defconf_dir))
                if not utils.is_hidden(defconf_dir)
            ]
        )
    else:
        job_doc.status = models.BUILD_STATUS
        job_doc.created_on = datetime.now(tz=tz_util.utc)

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
            if isinstance(defconf_doc, modj.JobDocument):
                idx += 1
            elif (isinstance(defconf_doc, moddf.DefconfigDocument) and
                    defconf_doc.metadata):
                for key in job_doc.METADATA_KEYS:
                    if key in defconf_doc.metadata.keys():
                        job_doc.metadata[key] = \
                            defconf_doc.metadata[key]
                break
            else:
                idx += 1

    return (docs, job_name)


def _traverse_defconf_dir(job, kernel, kernel_dir, defconfig_dir):
    """Traverse the defconfig directory looking for files.

    :param kernel_dir: The parent directory of this defconfig.
    :param defconfig_dir: The actual defconfig directory to parse.
    :return A `DefconfigDocument` instance.
    """
    # Default to the directory name and if we have the metadata file, get
    # the value from there.
    # Split on the + sign since some dirs are in the form 'defconfig+FRAGMENT'.
    defconfig = defconfig_dir.split('+')[0]
    dirname = defconfig_dir

    defconf_doc = moddf.DefconfigDocument(job, kernel, defconfig)
    defconf_doc.dirname = dirname

    utils.LOG.info("Traversing directory %s", dirname)

    real_dir = os.path.join(kernel_dir, dirname)
    defconf_doc.created_on = datetime.fromtimestamp(
        os.stat(real_dir).st_mtime, tz=tz_util.utc
    )

    for dirname, subdirs, files in os.walk(real_dir):
        # Consider only the actual directory and its files.
        subdirs[:] = []

        # Legacy: status was retrieved via the presence of a file.
        # Keep it for backward compatibility.
        if os.path.isfile(os.path.join(dirname, models.BUILD_PASS_FILE)):
            defconf_doc.status = models.PASS_STATUS
        elif os.path.isfile(os.path.join(dirname, models.BUILD_FAIL_FILE)):
            defconf_doc.status = models.FAIL_STATUS
        else:
            defconf_doc.status = models.UNKNOWN_STATUS

        json_meta_file = os.path.join(dirname, models.BUILD_META_JSON_FILE)
        default_meta_file = os.path.join(dirname, models.BUILD_META_FILE)

        if os.path.isfile(json_meta_file):
            _parse_build_metadata(json_meta_file, defconf_doc)
        elif os.path.isfile(default_meta_file):
            _parse_build_metadata(default_meta_file, defconf_doc)
        else:
            # If we do not have the metadata file, consider the build failed.
            defconf_doc.status = models.FAIL_STATUS

    return defconf_doc


def _parse_build_metadata(metadata_file, defconf_doc):
    """Parse the metadata file contained in thie build directory.

    :param metadata_file: The path to the metadata file.
    :param defconf_doc: The `DefconfigDocument` whose metadata will be updated.
    """
    metadata = utils.meta_parser.parse_metadata_file(metadata_file)

    if metadata:
        # Set some of the metadata values directly into the objet for easier
        # search.
        defconf_doc.status = metadata.get(models.BUILD_RESULT_KEY, None)
        defconf_doc.defconfig = metadata.get(models.DEFCONFIG_KEY, None)
        defconf_doc.warnings = metadata.get(models.WARNINGS_KEY, None)
        defconf_doc.errros = metadata.get(models.ERRORS_KEY, None)
        defconf_doc.arch = metadata.get(models.ARCHITECTURE_KEY, None)

    defconf_doc.metadata = metadata


def _import_all(database, base_path=utils.BASE_PATH):
    """This function is used only to trigger the import from the command line.

    Do not use it elsewhere.
    :param base_path: Where to start traversing directories. Defaults to:
        /var/www/images/kernel-ci.
    :return The docs to save. All docs are subclasses of `BaseDocument`.
    """

    docs = []

    for job_dir in os.listdir(base_path):
        job = job_dir
        job_dir = os.path.join(base_path, job_dir)

        if os.path.isdir(job_dir):
            for kernel_dir in os.listdir(job_dir):
                if os.path.isdir(os.path.join(job_dir, kernel_dir)):
                    all_docs, _ = _import_job(
                        job, kernel_dir, database, base_path
                    )
                    docs.extend(all_docs)

    return docs


if __name__ == '__main__':
    connection = pymongo.MongoClient()
    database = connection[models.DB_NAME]

    documents = _import_all(database)
    utils.db.save(database, documents)

    connection.disconnect()
