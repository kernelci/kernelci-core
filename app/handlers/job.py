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

import tornado

from functools import partial

from handlers.base import BaseHandler
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
            'POST': ['job', 'kernel'],
            'DELETE': ['job'],
        }

        return valid_keys.get(method, None)

    def _post(self, json_obj):
        import_job.apply_async([json_obj], link=send_emails.s())
        self._create_valid_response(200)

    def _delete(self, json_obj):
        self.executor.submit(
            partial(self._delete_job, json_obj['job'])).add_done_callback(
                lambda future:
                tornado.ioloop.IOLoop.instance().add_callback(
                    partial(self._create_valid_response, future.result()))
            )

    def _delete_job(self, job_id):
        """Delete a job from the database.

        Use with care since documents cannot be retrieved after!

        Removing a job from the collection means to remove also all the
        other documents associated with the it: defconfig and subscription.

        :param job_id: The ID of the job to remove.
        :return Whatever is returned by the `delete` function.
        """
        # TODO: maybe look into two-phase commits in mongodb
        # http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/

        ret_val = 200

        if find_one(self.collection, job_id):
            delete(
                self.db[DEFCONFIG_COLLECTION],
                {'job_id': {'$in': [job_id]}}
            )

            delete(
                self.db[SUBSCRIPTION_COLLECTION],
                {'job_id': {'$in': [job_id]}}
            )

            ret_val = delete(self.collection, job_id)
        else:
            ret_val = 404

        return ret_val
