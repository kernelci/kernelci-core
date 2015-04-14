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

try:
    import simplejson as json
except ImportError:
    import json

import argparse
import os
import sys

import models
import utils
import utils.db
import utils.log_parser


def main(job, kernel=None):
    status = 0

    database = utils.db.get_db_connection({})

    if kernel:
        spec = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel
        }
        job_doc = utils.db.find_one2(
            database[models.JOB_COLLECTION],
            spec,
            [models.ID_KEY]
        )

        if job_doc:
            job_id = job_doc[models.ID_KEY]

            json_obj = {
                models.JOB_KEY: job,
                models.KERNEL_KEY: kernel
            }
            utils.log_parser.parse_build_log(
                job_id, json_obj, {})
        else:
            utils.LOG.error("Cannot find job ID for %s-%s", job, kernel)
            status = 1
    else:
        start_path = os.path.join(utils.BASE_PATH, job)
        if os.path.isdir(start_path):
            for dirname, subdirs, files in os.walk(start_path):
                base_name = os.path.basename(dirname)

                if dirname == start_path:
                    continue

                if base_name.startswith("."):
                    continue

                if any(["build.json" not in files, "build.log" not in files]):
                    continue

                build_json = os.path.join(dirname, "build.json")
                build_log = os.path.join(dirname, utils.BUILD_LOG_FILE)

                kernel = None

                if all([
                        os.path.isfile(build_log),
                        os.path.isfile(build_json)]):
                    build_data = None
                    with open(build_json, "r") as json_data:
                        build_data = json.load(json_data)

                    new_kernel = build_data.get(models.GIT_DESCRIBE_KEY)

                    if new_kernel:
                        if new_kernel != kernel:
                            kernel = new_kernel

                            spec = {
                                models.JOB_KEY: job,
                                models.KERNEL_KEY: kernel
                            }
                            job_doc = utils.db.find_one2(
                                database[models.JOB_COLLECTION],
                                spec,
                                [models.ID_KEY]
                            )

                        if job_doc:
                            job_id = job_doc[models.ID_KEY]

                            json_obj = {
                                models.JOB_KEY: job,
                                models.KERNEL_KEY: kernel
                            }
                            utils.log_parser.parse_build_log(
                                job_id, json_obj, {})
                        else:
                            status = 1
                            utils.LOG.error(
                                "Job ID missing for %s", dirname)
                    else:
                        status = 1
                        utils.LOG.error(
                            "Missing kernel key in the build json file for %s",
                            dirname)
        else:
            status = 1
            utils.LOG.error("Cannot find directory for job %s", job)

    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse build logs",
        version=0.1
    )
    parser.add_argument(
        "--job", "-j",
        type=str,
        help="The name of the job/tree",
        dest="job",
        required=True,
    )
    parser.add_argument(
        "--kernel", "-k",
        type=str,
        help="The name of the kernel",
        dest="kernel",
        default=None,
    )

    args = parser.parse_args()
    job = args.job
    kernel = args.kernel

    sys.exit(main(job, kernel))
