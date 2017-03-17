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

"""The RequestHandler for /job URLs."""

import bson

import handlers.base as hbase
import handlers.response as hresponse
import models
import taskqueue.tasks.build as taskb
import utils
import utils.db

JOB_NOT_FOUND = "Job '%s-%s (branch %s)' not found"
INTERNAL_ERROR = \
    "Internal error while searching/updating job '%s-%s' (branch %s)"
JOB_UPDATED = "Job '%s-%s' (branch %s) marked as '%s'"
INVALID_STATUS = "Status value '%s' is not valid, should be one of: %s"


# pylint: disable=too-many-public-methods
class JobHandler(hbase.BaseHandler):
    """Handle the /job URLs."""

    def __init__(self, application, request, **kwargs):
        super(JobHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.JOB_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.JOB_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()

        obj = kwargs["json_obj"]

        job = obj.get(models.JOB_KEY)
        kernel = obj.get(models.KERNEL_KEY)
        git_branch = utils.clean_branch_name(obj.get(models.GIT_BRANCH_KEY))
        status = obj.get(models.STATUS_KEY, None)

        if not status:
            status = models.PASS_STATUS

        if (status in models.VALID_JOB_STATUS):
            ret_val = utils.db.find_and_update(
                self.collection,
                {
                    models.GIT_BRANCH_KEY: git_branch,
                    models.JOB_KEY: job,
                    models.KERNEL_KEY: kernel
                },
                {models.STATUS_KEY: status}
            )

            if ret_val == 404:
                response.status_code = 404
                response.reason = JOB_NOT_FOUND % (job, kernel, git_branch)
            elif ret_val == 500:
                response.status_code = 500
                response.reason = INTERNAL_ERROR % (job, kernel, git_branch)
            else:
                response.reason = \
                    JOB_UPDATED % (job, kernel, git_branch, status)
                # Create the build logs summary file.
                taskb.create_build_logs_summary.apply_async(
                    [job, kernel, git_branch])
        else:
            response.status_code = 400
            response.reason = \
                INVALID_STATUS % (status, str(models.VALID_JOB_STATUS))

        return response

    def _delete(self, job_id, **kwargs):
        """Delete a job from the database.

        Use with care since documents cannot be retrieved after!

        Removing a job from the collection means to remove also all the
        other documents associated with the it: builds (and boots).

        :param job_id: The ID of the job to remove.
        :return Whatever is returned by the `utils.db.delete` function.
        """
        # TODO: maybe look into two-phase commits in mongodb
        # http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/
        response = hresponse.HandlerResponse()

        try:
            job_obj = bson.objectid.ObjectId(job_id)
            if utils.db.find_one2(self.collection, {models.ID_KEY: job_obj}):
                utils.db.delete(
                    self.db[models.BUILD_COLLECTION],
                    {models.JOB_ID_KEY: {"$eq": job_obj}}
                )

                response.status_code = utils.db.delete(
                    self.collection, job_obj)
                if response.status_code == 200:
                    response.reason = "Resource '%s' deleted" % job_id
            else:
                response.status_code = 404
                response.reason = self._get_status_message(404)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Invalid ID specified: %s", job_id)
            response.status_code = 400
            response.reason = "Wrong ID specified"

        return response
