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

from datetime import datetime

from models import DB_NAME
from models.defconfig import (
    DEFCONFIG_ACCEPTED_FILES,
    DefConfigDocument,
)
from models.job import JobDocument
from utils.db import save
from utils.log import get_log
from utils.utc import utc


BASE_PATH = '/var/www/images/kernel-ci'
# Filename that should be available when a job has finished.
JOB_DONE_FILE = '.done'

log = get_log()


def import_and_save(json_obj, base_path=BASE_PATH):
    """Wrapper function to be used as an external task.

    This function should only be called by Celery or other task managers.

    :param json_obj: The JSON object with the values to be parsed.
    :return The ID of the created document.
    """
    docs, job_id = import_job_from_json(json_obj, base_path)

    log.info(
        "Importing %d documents with job ID: %s" % (len(docs), job_id)
    )

    database = pymongo.MongoClient()[DB_NAME]

    try:
        save(database, docs)
    finally:
        database.connection.disconnect()

    return job_id


def import_job_from_json(json_obj, base_path=BASE_PATH):
    """Import a job based on the provided JSON object.

    The provided JSON object, a dict-like object, should contain at least the
    `job' and `kernel' keys. These keys will be used to traverse the directory
    structure found at the `/job/kernel' path (starting from the default
    location).

    :param json_obj: A dict-like object, that should contain the keys `job' and
                     `kernel'.
    :param base_path: The base path where to start constructing the traverse
                      directory. It defaults to: /var/www/images/kernel-ci.
    :return The documents to be saved, and the job document ID.
    """
    job_dir = json_obj['job']
    kernel_dir = json_obj['kernel']

    return _import_job(job_dir, kernel_dir, base_path)


def _import_job(job, kernel, base_path=BASE_PATH):
    """Traverse the job dir and create the documenst to save.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param base_path: The base path where to strat the traversing.
    :return The documents to be saved, and the job document ID.
    """
    job_dir = os.path.join(base_path, job, kernel)
    job_id = JobDocument.JOB_ID_FORMAT % (job, kernel)

    docs = []
    doc = JobDocument(job_id, job=job, kernel=kernel)
    doc.created = datetime.now(tz=utc).isoformat()

    docs.append(doc)

    if os.path.isdir(job_dir):
        if os.path.exists(os.path.join(job_dir, JOB_DONE_FILE)):
            # TODO: need to check if this will still be the case going forward.
            # TODO: what about failed jobs?
            doc.status = doc.JOB_DONE
        docs.extend(_traverse_defconf_dir(job_dir, job_id))
    else:
        # Job has been triggered, but there is no directory structure on the
        # filesystem: the job is being built.
        doc.status = doc.JOB_BUILDING

    return (docs, job_id)


def _traverse_defconf_dir(kernel_dir, job_id):
    """Traverse the defconfing directories.

    :param kernel_dir: The kernel dir where to start.
    :param job_id: The id of the JobDocument the defconfing will be linked to.
    :return A list of documents.
    """
    defconf_docs = []
    for defconf_dir in os.listdir(kernel_dir):
        defconf_doc = DefConfigDocument(defconf_dir, job_id)

        for dirname, subdirs, files in os.walk(
                os.path.join(kernel_dir, defconf_dir)):
            # Consider only the actual directory and its files.
            subdirs[:] = []
            for key, val in DEFCONFIG_ACCEPTED_FILES.iteritems():
                if key in files:
                    setattr(defconf_doc, val, os.path.join(dirname, key))
        defconf_docs.append(defconf_doc)

    return defconf_docs


def _import_all(base_path=BASE_PATH):
    """This function is used only to trigger the import from the command line.

    Do not use it elsewhere.
    :param base_path: Where to start traversing directories. Defaults to:
                      /var/www/images/kernel-ci.
    :return The docs to save. All docs are subclasses of BaseDocument.
    """

    docs = []

    for job_dir in os.listdir(base_path):
        job_id = job_dir
        job_dir = os.path.join(base_path, job_dir)

        for kernel_dir in os.listdir(job_dir):
            doc_id = JobDocument.JOB_ID_FORMAT % (job_id, kernel_dir)
            job_doc = JobDocument(doc_id, job=job_id, kernel=kernel_dir)
            job_doc.created = datetime.now(tz=utc).isoformat()
            docs.append(job_doc)

            kernel_dir = os.path.join(job_dir, kernel_dir)

            docs.extend(_traverse_defconf_dir(kernel_dir, doc_id))

    return docs


if __name__ == '__main__':
    connection = pymongo.MongoClient()
    database = connection[DB_NAME]

    documents = _import_all()
    save(database, documents)

    connection.disconnect()
