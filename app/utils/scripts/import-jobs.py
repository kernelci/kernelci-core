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

"""Basic command line script to import jobs."""

import argparse
import os
import sys

import utils
import utils.docimport as docimport


def _is_dir(path):
    return os.path.isdir(path)


def import_all(database, base_path=utils.BASE_PATH):
    docs = []

    for job_dir in os.listdir(base_path):
        job = job_dir
        job_dir = os.path.join(base_path, job_dir)

        if _is_dir(job_dir):
            for kernel_dir in os.listdir(job_dir):
                if _is_dir(os.path.join(job_dir, kernel_dir)):
                    all_docs, _ = docimport._import_job(
                        job, kernel_dir, database, base_path
                    )
                    docs.extend(all_docs)

    if docs:
        utils.db.save_all(database, docs, manipulate=True)
    else:
        utils.LOG.error("No jobs found to be imported")
        sys.exit(1)


def import_with_job(job, database, base_path=utils.BASE_PATH):
    job_dir = os.path.join(base_path, job)

    if _is_dir(job_dir):
        for kernel in os.listdir(job_dir):
            docs, job_id = docimport._import_job(
                job, kernel, database, base_path=base_path)

            if docs:
                utils.db.save_all(database, docs, manipulate=True)
            else:
                utils.LOG.info("No jobs/defconfigs to save")
    else:
        utils.LOG.error("Prpvided job '%s' does not exist")
        sys.exit(1)


def import_with_job_and_kernel(
        job, kernel, database, base_path=utils.BASE_PATH):

    job_dir = os.path.join(base_path, job)
    kernel_dir = os.path.join(job_dir, kernel)

    if all([_is_dir(job_dir), _is_dir(kernel_dir)]):
        docs, job_id = docimport._import_job(
            job, kernel, database, base_path=base_path)

        if docs:
            utils.db.save_all(database, docs, manipulate=True)
        else:
            utils.LOG.info("No jobs/defconfigs to save")
    else:
        utils.LOG.error(
            "Provided job (%s) and kernel (%s) do not exist",
            job, kernel)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Import jobs from disk",
        version=0.1
    )
    parser.add_argument(
        "--job", "-j",
        type=str,
        help="The name of the job to import",
        dest="job"
    )
    parser.add_argument(
        "--kernel", "-k",
        type=str,
        help="The name of the kernel to import",
        dest="kernel"
    )
    parser.add_argument(
        "--base-path", "-b",
        type=str,
        help="The (absolute) base path where to start looking for jobs",
        default=utils.BASE_PATH,
        dest="base_path"
    )

    args = parser.parse_args()

    job = args.job
    kernel = args.kernel
    base_path = args.base_path

    database = utils.db.get_db_connection({})
    if all([job is None, kernel is None]):
        import_all(database, base_path=base_path)
    elif all([job is not None, kernel is None]):
        import_with_job(job, database, base_path=base_path)
    elif all([job is not None, kernel is not None]):
        import_with_job_and_kernel(job, kernel, database, base_path=base_path)
    else:
        utils.LOG.info("Nothing to do")
        sys.exit(1)

if __name__ == "__main__":
    main()
