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

"""The RequestHandler for /job URLs."""

from handlers.base import BaseHandler
from handlers.response import HandlerResponse
from models import (
    CREATED_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    PRIVATE_KEY,
    STATUS_KEY,
)
from models.job import JOB_COLLECTION
from models.defconfig import DEFCONFIG_COLLECTION
from models.subscription import SUBSCRIPTION_COLLECTION
from utils.db import (
    delete,
    find_one,
)
from taskqueue.tasks import (
    send_emails,
    import_job,
)


class JobHandler(BaseHandler):
    """Handle the /job URLs."""

    def __init__(self, application, request, **kwargs):
        super(JobHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[JOB_COLLECTION]

    def _valid_keys(self, method):
        valid_keys = {
            'POST': [JOB_KEY, KERNEL_KEY],
            'GET': [
                JOB_KEY, KERNEL_KEY, STATUS_KEY, PRIVATE_KEY, CREATED_KEY,
            ],
        }

        return valid_keys.get(method, None)

    def _post(self, *args, **kwargs):
        response = HandlerResponse(202)
        response.reason = "Request accepted and being imported"
        response.result = None

        import_job.apply_async([kwargs['json_obj']], link=send_emails.s())

        return response

    def _delete(self, job_id):
        """Delete a job from the database.

        Use with care since documents cannot be retrieved after!

        Removing a job from the collection means to remove also all the
        other documents associated with the it: defconfig and subscription.

        :param job_id: The ID of the job to remove.
        :return Whatever is returned by the `utils.db.delete` function.
        """
        # TODO: maybe look into two-phase commits in mongodb
        # http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/
        response = HandlerResponse()
        response.result = None

        if find_one(self.collection, job_id):
            delete(
                self.db[DEFCONFIG_COLLECTION],
                {JOB_ID_KEY: {'$in': [job_id]}}
            )

            delete(
                self.db[SUBSCRIPTION_COLLECTION],
                {JOB_ID_KEY: {'$in': [job_id]}}
            )

            response.status_code = delete(self.collection, job_id)
            if response.status_code == 200:
                response.reason = "Resource '%s' deleted" % job_id
        else:
            response.status_code = 404
            response.reason = self._get_status_message(404)

        return response
