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

"""All build/job related celery tasks."""

import taskqueue.celery as taskc
import utils.build
import utils.log_parser
import utils.logs.build


@taskc.app.task(name="import-build")
def import_build(json_obj):
    """Import a single build document.

    This is used to provide a Celery-task access to the import function.

    :param json_obj: The JSON object with the values necessary to import the
    build data.
    :type json_obj: dictionary
    :param db_options: The database connection options.
    :type db_options: dictionary
    :return The build ID and the job ID.
    """
    # build_id and job_id are necessary since they are injected by Celery into
    # another function.
    build_id, job_id, errors = utils.build.import_single_build(
        json_obj, taskc.app.conf.db_options)
    # TODO: handle errors.
    return build_id, job_id


@taskc.app.task(name="parse-single-build-log")
def parse_single_build_log(prev_res):
    """Wrapper around the real build log parsing function.

    Used to provided a task to the import function.

    :param prev_res: The results of the previous task, that should be a list
    with two elements: the build ID and the job ID.
    :type prev_res: list
    :param db_options: The database connection parameters.
    :type db_options: dictionary
    :return A 2-tuple: The status code, and the errors data structure.
    """
    status, errors = utils.log_parser.parse_single_build_log(
        prev_res[0], prev_res[1], taskc.app.conf.db_options)
    # TODO: handle errors.
    return status


@taskc.app.task(name="create-logs-summary")
def create_build_logs_summary(job, kernel, git_branch):
    """Task wrapper around the real function.

    Create the build logs summary.

    :param job: The tree value.
    :type job: str
    :param kernel: The kernel value.
    :type kernel: str
    :param git_branch: The branch name.
    :type git_branch: str
    """
    # TODO: handle error
    status, error = utils.logs.build.create_build_logs_summary(
        job, kernel, git_branch, taskc.app.conf.db_options)
    return status
