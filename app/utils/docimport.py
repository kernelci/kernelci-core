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

import os
import pymongo

from bson import tz_util
from datetime import datetime

from models import (
    BUILDING_STATUS,
    BUILD_FAIL_FILE,
    BUILD_META_FILE,
    BUILD_PASS_FILE,
    DB_NAME,
    DONE_FILE,
    DONE_STATUS,
    FAILED_STATUS,
    SUCCESS_STATUS,
    UNKNOWN_STATUS,
)
from models.defconfig import (
    DEFCONFIG_ACCEPTED_FILES,
    DefConfigDocument,
)
from models.job import (
    JOB_COLLECTION,
    JobDocument,
)
from utils import (
    BASE_PATH,
    LOG,
)
from utils.db import (
    find_one,
    save,
)


def import_and_save_job(json_obj, base_path=BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.

    :param json_obj: The JSON object with the values to be parsed.
    :return The ID of the created document.
    """
    database = pymongo.MongoClient()[DB_NAME]
    docs, job_id = import_job_from_json(json_obj, database, base_path)

    if docs:
        LOG.info(
            "Importing %d documents with job ID: %s", len(docs), job_id
        )

        try:
            save(database, docs)
        finally:
            database.connection.disconnect()
    else:
        LOG.info("No jobs to save")

    return job_id


def import_job_from_json(json_obj, database, base_path=BASE_PATH):
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
    job_dir = json_obj['job']
    kernel_dir = json_obj['kernel']

    return _import_job(job_dir, kernel_dir, database, base_path)


def _import_job(job, kernel, database, base_path=BASE_PATH):
    """Traverse the job dir and create the documenst to save.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param base_path: The base path where to strat the traversing.
    :return The documents to be saved, and the job document ID.
    """
    job_dir = os.path.join(base_path, job)
    kernel_dir = os.path.join(job_dir, kernel)
    job_id = JobDocument.ID_FORMAT % {'job': job, 'kernel': kernel}

    docs = []

    saved_doc = find_one(database[JOB_COLLECTION], [job_id])
    if saved_doc:
        job_doc = JobDocument.from_json(saved_doc)
    else:
        job_doc = JobDocument(job_id, job=job, kernel=kernel)

    job_doc.updated = datetime.now(tz=tz_util.utc)
    docs.append(job_doc)

    if os.path.exists(os.path.join(job_dir, DONE_FILE)):
        job_doc.status = DONE_STATUS
    else:
        job_doc.status = BUILDING_STATUS

    if os.path.isdir(kernel_dir):
        if os.path.exists(os.path.join(kernel_dir, DONE_FILE)):
            job_doc.status = DONE_STATUS

        # If the job dir exists, read the last modification time from the
        # file system and use that as the creation date.
        if not job_doc.created:
            job_doc.created = datetime.fromtimestamp(
                os.stat(kernel_dir).st_mtime, tz=tz_util.utc)

        job_doc.updated = datetime.now(tz=tz_util.utc)

        docs.extend(
            [
                _traverse_defconf_dir(
                    job_id, job, kernel, kernel_dir, defconf_dir
                ) for defconf_dir in os.listdir(kernel_dir)
                if os.path.isdir(os.path.join(kernel_dir, defconf_dir))
            ]
        )
    else:
        job_doc.created = datetime.now(tz=tz_util.utc)

    # Kind of a hack:
    # We want to store some metadata at the job document level as well, like
    # git tree, git commit...
    # Since, at the moment, we do not have the build.meta file at the job level
    # we need to pick one from the build documents, and extract some values.
    docs_len = len(docs)
    if docs_len > 1:
        idx = 0
        while idx < docs_len:
            defconf_doc = docs[idx]
            if isinstance(defconf_doc, JobDocument):
                idx += 1
            elif (isinstance(defconf_doc, DefConfigDocument) and
                    defconf_doc.metadata):
                for key in job_doc.METADATA_KEYS:
                    if key in defconf_doc.metadata.keys():
                        job_doc.metadata[key] = \
                            defconf_doc.metadata[key]
                break
            else:
                idx += 1

    return (docs, job_id)


def _traverse_defconf_dir(job_id, job, kernel, kernel_dir, defconf_dir):
    """Traverse the defconfig directory looking for files.

    :param job_id: The ID of the parent job.
    :param kernel_dir: The parent directory of this defconfig.
    :param defconf_dir: The actual defconfig directory to parse.
    :return A `DefConfigDocument` instance.
    """
    defconf_doc = DefConfigDocument(defconf_dir, job_id, job, kernel)

    LOG.info("Traversing directory %s", defconf_dir)

    real_dir = os.path.join(kernel_dir, defconf_dir)
    defconf_doc.created = datetime.fromtimestamp(
        os.stat(real_dir).st_mtime, tz=tz_util.utc
    )

    for dirname, subdirs, files in os.walk(real_dir):
        # Consider only the actual directory and its files.
        subdirs[:] = []
        for key, val in DEFCONFIG_ACCEPTED_FILES.iteritems():
            if key in files:
                setattr(defconf_doc, val, os.path.join(dirname, key))

        # Legacy: status was retrieved via the presence of a file.
        # Keep it for backward compatibility.
        if os.path.exists(os.path.join(dirname, BUILD_PASS_FILE)):
            defconf_doc.status = SUCCESS_STATUS
        elif os.path.exists(os.path.join(dirname, BUILD_FAIL_FILE)):
            defconf_doc.status = FAILED_STATUS
        else:
            defconf_doc.status = UNKNOWN_STATUS

        if os.path.exists(os.path.join(dirname, BUILD_META_FILE)):
            _parse_build_metadata(
                os.path.join(dirname, BUILD_META_FILE), defconf_doc
            )
        else:
            # If we do not have the metadata file, consider the build failed.
            defconf_doc.status = FAILED_STATUS

    return defconf_doc


def _parse_build_metadata(metadata_file, defconf_doc):
    """Parse the metadata file contained in thie build directory.

    :param metadata_file: The path to the metadata file.
    :param defconf_doc: The `DefConfigDocument` whose metadata will be updated.
    """
    metadata = {}

    LOG.info("Parsing metadata file %s", metadata_file)

    with open(metadata_file, 'r') as r_file:
        for line in r_file:
            line = line.strip()
            if line:
                if line[0] == '#':
                    # Accept a sane char for commented lines.
                    continue

                try:
                    key, value = line.split(':', 1)
                    value = value.strip()
                    if value:
                        # We store only real values, not empty ones.
                        metadata[key] = value
                except ValueError, ex:
                    LOG.error("Error parsing metadata file line: %s", line)
                    LOG.exception(str(ex))

    if metadata.get('build_result', None):
        status = metadata.get('build_result')
        if status == 'PASS':
            defconf_doc.status = SUCCESS_STATUS
        elif status == 'FAIL':
            defconf_doc.status = FAILED_STATUS

    defconf_doc.metadata = metadata


def _import_all(database, base_path=BASE_PATH):
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
    database = connection[DB_NAME]

    documents = _import_all(database)
    save(database, documents)

    connection.disconnect()
