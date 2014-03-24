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

import os
import pymongo

from models import (
    DB_NAME,
    DefConfigDocument,
    JobDocument,
)


BASE_PATH = '/var/www/images/kernel-ci'


def import_job_from_json(json_doc, db, base_path=BASE_PATH):
    pass


def import_job(job, kernel, db, base_path=BASE_PATH):
    job_dir = os.path.join(base_path, job, kernel)
    job_id = JobDocument.JOB_ID_FORMAT % (job, kernel)

    docs = JobDocument(job_id)

    if os.path.isdir(job_dir):
        docs.extend(traverse_defconf_dir(job_dir, job_id))

    import_jobs(db, docs)


def traverse_defconf_dir(job_dir, job_id):
    defconf_docs = []
    for defconf_dir in os.listdir(job_dir):
        defconf_doc = DefConfigDocument(defconf_dir)
        defconf_doc.job_id = job_id
        defconf_docs.append(defconf_doc)
    return defconf_docs


def import_all(base_path=BASE_PATH):

    docs = []

    for job_dir in os.listdir(base_path):
        job_id = job_dir
        job_dir = os.path.join(base_path, job_dir)

        for kernel_dir in os.listdir(job_dir):
            job_id = JobDocument.JOB_ID_FORMAT % (job_id, kernel_dir)
            job_doc = JobDocument(job_id)
            docs.append(job_doc)

            kernel_dir = os.path.join(job_dir, kernel_dir)

            docs.extend(traverse_defconf_dir(kernel_dir, job_id))

    return docs


def import_jobs(db, documents):
    for document in documents:
        db[document.collection].save(document.to_dict())

if __name__ == '__main__':
    conn = pymongo.MongoClient()
    db = conn[DB_NAME]

    docs = import_all()
    import_jobs(db, docs)

    conn.disconnect()
