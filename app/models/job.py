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

"""The model that represents a job document in the mongodb collection."""

import bson
import types

import models
import models.base as modb


# pylint: disable=invalid-name
class JobDocument(modb.BaseDocument):
    """This class represents a job as seen on the file system.

    Each job on the file system is composed of a real job name (usually who
    triggered the job), and a kernel directory. This job is the combination
    of the two, and its name is of the form `job-kernel`.
    """

    def __init__(self, job, kernel):

        doc_name = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
        }
        self._name = models.JOB_DOCUMENT_NAME % doc_name
        self._job = job
        self._kernel = kernel

        self._id = None
        self._created_on = None

        self._private = False
        self._status = None

    @property
    def collection(self):
        return models.JOB_COLLECTION

    @property
    def name(self):
        """The name of the boot report."""
        return self._name

    @property
    def id(self):
        """The ID of this object as returned by mongodb."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the ID of this object with the ObjectID from mongodb.

        :param value: The ID of this object.
        :type value: str
        """
        self._id = value

    @property
    def created_on(self):
        """When this object was created."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this object.

        :param value: The lab creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

    @property
    def private(self):
        """If the job is private or not.

        :return True or False
        """
        return self._private

    @private.setter
    def private(self, value):
        """Set the private attribute."""
        self._private = value

    @property
    def job(self):
        """The real job name as found on the file system."""
        return self._job

    @property
    def kernel(self):
        """The real kernel name as found on the file system."""
        return self._kernel

    @property
    def status(self):
        """The status of the job."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status of the job.

        :param value: The status.
        """
        if not value in models.VALID_JOB_STATUS:
            raise ValueError(
                "Status value '%s' not valid, should be one of: %s",
                value, str(models.VALID_JOB_STATUS)
            )
        self._status = value

    def to_dict(self):
        job_dict = {
            models.CREATED_KEY: self.created_on,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.NAME_KEY: self.name,
            models.PRIVATE_KEY: self.private,
            models.STATUS_KEY: self.status,
        }

        if self.id:
            job_dict[models.ID_KEY] = self.id

        return job_dict

    @staticmethod
    def from_json(json_obj):
        """Build a document from a JSON object.

        :param json_obj: The JSON object to start from, or a JSON string.
        :return An instance of `JobDocument` or None
        """
        job_doc = None

        if isinstance(json_obj, types.StringTypes):
            json_obj = bson.json_util.loads(json_obj)

        # pylint: disable=maybe-no-member
        if isinstance(json_obj, types.DictionaryType):
            job_pop = json_obj.pop
            job = job_pop(models.JOB_KEY)
            kernel = job_pop(models.KERNEL_KEY)
            doc_id = job_pop(models.ID_KEY)
            # Remove the name key.
            job_pop(models.NAME_KEY)

            job_doc = JobDocument(job, kernel)
            job_doc.id = doc_id

            for key, value in json_obj.iteritems():
                setattr(job_doc, key, value)

        return job_doc
