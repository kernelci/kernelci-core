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

"""Basic command line script to import boots."""

import argparse
import glob
import os
import sys

import utils
import utils.bootimport as bootimport


def _is_dir(path):
    return os.path.isdir(path)


def parse_boot_from_disk(
        job, kernel, lab_name, database, base_path):
    """Traverse the kernel directory and look for boot report logs.

    :param job: The name of the job.
    :param kernel: The name of the kernel.
    :param lab_name: The name of the lab.
    :param base_path: The base path where to start traversing.
    :return A list of documents to be saved, or an empty list.
    """
    docs = []

    job_dir = os.path.join(base_path, job)

    if not utils.is_hidden(job) and _is_dir(job_dir):
        kernel_dir = os.path.join(job_dir, kernel)

        if not utils.is_hidden(kernel) and _is_dir(kernel_dir):
            for defconfig in os.listdir(kernel_dir):
                defconfig_dir = os.path.join(kernel_dir, defconfig)

                if not utils.is_hidden(defconfig) and \
                        _is_dir(defconfig_dir):

                    lab_dir = os.path.join(defconfig_dir, lab_name)
                    if _is_dir(lab_dir):
                        docs.extend([
                            bootimport._parse_boot_from_file(boot_log, database)
                            for boot_log in glob.iglob(
                                os.path.join(lab_dir, utils.BOOT_REPORT_PATTERN)
                            )
                            if os.path.isfile(boot_log)
                        ])

    return docs


def import_with_lab_name(lab_name, database, base_path):
    """Handy function to import all boot logs for a single lab.

    :param lab_name: The lab name whose boot reports should be imported.
    :type lab_name: str
    :param base_path: Where to start the scan on the hard disk.
    :type base_path: str
    :return A list of BootDocument documents.
    """
    docs = []

    for job in os.listdir(base_path):
        job_dir = os.path.join(base_path, job)

        for kernel in os.listdir(job_dir):
            docs.extend(
                parse_boot_from_disk(job, kernel, lab_name, database, base_path)
            )

    if docs:
        utils.db.save_all(database, docs, manipulate=True)
    else:
        utils.LOG.info("No boot reports to save")


def import_with_job_and_kernel(job, kernel, lab_name, database, base_path):
    job_dir = os.path.join(base_path, job)
    kernel_dir = os.path.join(job_dir, kernel)

    docs = []

    if all([_is_dir(job_dir), _is_dir(kernel_dir)]):
        for kernel in os.listdir(job_dir):
            docs.extend(
                parse_boot_from_disk(job, kernel, lab_name, database, base_path)
            )

        if docs:
            utils.db.save_all(database, docs, manipulate=True)
        else:
            utils.LOG.info("No boot reports to save")
    else:
        utils.LOG.error(
            "Provided job (%s) and kernel (%s) do not exist",
            job, kernel
        )
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import boots from disk",
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
        "--lab-name", "-l",
        type=str,
        help="The name of the lab to consider",
        required=True,
        dest="lab_name"
    )
    parser.add_argument(
        "--base-path", "-b",
        type=str,
        help="The (absolute) base path where to start looking for jobs",
        default=utils.BASE_PATH,
        dest="base_path"
    )

    args = parser.parse_args()

    lab_name = args.lab_name
    kernel = args.kernel
    job = args.job
    base_path = args.base_path

    database = utils.db.get_db_connection({})
    if all([kernel is None, job is None]):
        import_with_lab_name(lab_name, database, base_path)
    elif all([job is not None, kernel is not None]):
        import_with_job_and_kernel(job, kernel, lab_name, database, base_path)
    else:
        utils.LOG.error("Not all cases have been implemented!")
        sys.exit(1)
