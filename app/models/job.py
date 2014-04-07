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

from models import ID_KEY
from models.base import BaseDocument

JOB_COLLECTION = 'job'


class JobDocument(BaseDocument):
    """This class represents a job as seen on the file system.

    Each job on the file system is composed of a real job name (usually who
    triggered the job), and a kernel directory. This job is the combination
    of the two, and its name is of the form `job-kernel`.
    """

    JOB_ID_FORMAT = '%s-%s'
    JOB_BUILDING = 'BUILDING'
    JOB_DONE = 'DONE'
    JOB_FAILED = 'FAILED'

    def __init__(self, name, job=None, kernel=None):
        super(JobDocument, self).__init__(name)

        self._private = False
        self._job = job
        self._kernel = kernel
        self._status = None
        self._created = None
        self._updated = None

    @property
    def collection(self):
        return JOB_COLLECTION

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
        """Return the real job name as found on the file system."""
        return self._job

    @job.setter
    def job(self, value):
        """Set the real job name as found on the file system."""
        self._job = value

    @property
    def kernel(self):
        """Return the real kernel name as found on the file system."""
        return self._kernel

    @kernel.setter
    def kernel(self, value):
        """Set the real kernel name as found on the file system."""
        self._kernel = value

    @property
    def created(self):
        """Return the date this document was created.

        :return A string representing a datetime object in ISO format,
                UTC time zone.
        """
        return self._created

    @created.setter
    def created(self, value):
        """Set the date this document was created.

        :param value: A string representing a datetime object in ISO format.
        """
        self._created = value

    @property
    def updated(self):
        """The date this document was last updated.

        :return A string representing a datetime object in ISO format,
                UTC time zone.
        """
        return self._updated

    @updated.setter
    def updated(self, value):
        """Set the date this document was last updated.

        :param value: A string representing a datetime object in ISO format.
        """
        self._updated = value

    @property
    def status(self):
        """The build status of this job."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the build status of the job.

        :param value: The status.
        """
        self._status = value

    def to_dict(self):
        job_dict = super(JobDocument, self).to_dict()
        job_dict['private'] = self._private
        job_dict['job'] = self._job
        job_dict['kernel'] = self._kernel
        job_dict['created'] = self._created
        job_dict['updated'] = self._updated
        job_dict['status'] = self._status
        return job_dict

    @staticmethod
    def from_json(json_obj):
        name = json_obj.pop(ID_KEY)

        job_doc = JobDocument(name)
        for key, value in json_obj.iteritems():
            setattr(job_doc, key, value)

        return job_doc
