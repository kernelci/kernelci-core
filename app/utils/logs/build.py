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

import io
import itertools
import os

import models
import utils
import utils.db


def create_build_logs_summary(job, kernel, db_options):
    """Create a summary TXT file with the errors/warnings found in the log.

    :param job: The tree value.
    :type job: str
    :param kernel: The kernel value.
    :type kernel: str
    :param db_options: The database connection parameters.
    :type db_options: dict
    """
    ret_val = 200
    error = ""

    db_conn = utils.db.get_db_connection(db_options)

    result = utils.db.find_one2(
        db_conn[models.ERRORS_SUMMARY_COLLECTION],
        {"job": job, "kernel": kernel}
    )

    if result:
        errors = result.get(models.ERRORS_KEY)
        warnings = result.get(models.WARNINGS_KEY)
        mismatches = result.get(models.MISMATCHES_KEY)

        if any([errors, warnings, mismatches]):
            file_path = os.path.join(
                utils.BASE_PATH, job, kernel, "build-logs-summary.txt")

            try:
                with io.open(file_path, mode="w") as to_write:
                    for line in itertools.chain(errors, warnings, mismatches):
                        to_write.write(
                            u"{:>4d} {:s}\n".format(line[0], line[1]))
            except IOError, ex:
                ret_val = 500
                error = (
                    "Error writing logs summary for {:s}-{:s}: {:s}".format(
                        job, kernel, ex.strerror))

                utils.LOG.error(error)
        else:
            utils.LOG.info("No errors/warnings found for %s-%s", job, kernel)
    else:
        utils.LOG.info("No errors summary found for %s-%s", job, kernel)

    return ret_val, error
