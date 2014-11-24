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

        self._created_on = None
        self._id = None
        self._name = models.JOB_DOCUMENT_NAME % doc_name
        self._version = None

        self._job = job
        self._kernel = kernel
        self.git_branch = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.private = False
        self.status = None

    @property
    def collection(self):
        return models.JOB_COLLECTION

    @property
    def name(self):
        """The name of the object."""
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
        if value is not None and value not in models.VALID_JOB_STATUS:
            raise ValueError(
                "Status value '%s' not valid, should be one of: %s",
                value, str(models.VALID_JOB_STATUS)
            )
        self._status = value

    @property
    def version(self):
        """The schema version of this object."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this object.

        :param value: The schema string.
        :type param: str
        """
        self._version = value

    @property
    def git_url(self):
        """The git URL where the code comes from."""
        return self._git_url

    @git_url.setter
    def git_url(self, value):
        """Set the git URL of this defconfig document."""
        self._git_url = value

    @property
    def git_commit(self):
        """The git commit SHA."""
        return self._git_commit

    @git_commit.setter
    def git_commit(self, value):
        """Set the git commit SHA."""
        self._git_commit = value

    @property
    def git_branch(self):
        """The branch name of the repository used."""
        return self._git_branch

    @git_branch.setter
    def git_branch(self, value):
        """Set the branch name of the repository used."""
        self._git_branch = value

    @property
    def git_describe(self):
        """The git describe value of the repository."""
        return self._git_describe

    @git_describe.setter
    def git_describe(self, value):
        """Set the git describe value of the repository."""
        self._git_describe = value

    def to_dict(self):
        job_dict = {
            models.CREATED_KEY: self.created_on,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_URL_KEY: self.git_url,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.NAME_KEY: self.name,
            models.PRIVATE_KEY: self.private,
            models.STATUS_KEY: self.status,
            models.VERSION_KEY: self.version,
        }

        if self.id:
            job_dict[models.ID_KEY] = self.id

        return job_dict

    @staticmethod
    def from_json(json_obj):
        """Build a document from a JSON object.

        :param json_obj: The JSON object to start from.
        :return An instance of `JobDocument` or None
        """
        job_doc = None

        # pylint: disable=maybe-no-member
        if json_obj and isinstance(json_obj, types.DictionaryType):
            json_get = json_obj.get
            job = json_get(models.JOB_KEY)
            kernel = json_get(models.KERNEL_KEY)

            job_doc = JobDocument(job, kernel)

            job_doc.created_on = json_get(models.CREATED_KEY, None)
            job_doc.git_branch = json_get(models.GIT_BRANCH_KEY, None)
            job_doc.git_commit = json_get(models.GIT_COMMIT_KEY, None)
            job_doc.git_describe = json_get(models.GIT_DESCRIBE_KEY, None)
            job_doc.git_url = json_get(models.GIT_URL_KEY, None)
            job_doc.id = json_get(models.ID_KEY, None)
            job_doc.status = json_get(models.STATUS_KEY, None)
            job_doc.version = json_get(models.VERSION_KEY, "1.0")

        return job_doc
