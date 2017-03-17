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

import copy
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

    def __init__(self, job, kernel, git_branch, version="1.1"):
        self._created_on = None
        self._id = None
        self._version = version

        self.job = job
        self.kernel = kernel
        self.git_branch = git_branch

        self.compiler = None
        self.compiler_version = None
        self.compiler_version_ext = None
        self.compiler_version_full = None
        self.cross_compile = None
        self.git_commit = None
        self.git_describe = None
        self.git_describe_v = None
        self.git_url = None
        self.kernel_version = None
        self.private = False
        self.status = None

    @property
    def collection(self):
        return models.JOB_COLLECTION

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

    def to_dict(self):
        job_dict = {
            models.COMPILER_KEY: self.compiler,
            models.COMPILER_VERSION_EXT_KEY: self.compiler_version_ext,
            models.COMPILER_VERSION_FULL_KEY: self.compiler_version_full,
            models.COMPILER_VERSION_KEY: self.compiler_version,
            models.CREATED_KEY: self.created_on,
            models.CROSS_COMPILE_KEY: self.cross_compile,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_DESCRIBE_V_KEY: self.git_describe_v,
            models.GIT_URL_KEY: self.git_url,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.KERNEL_VERSION_KEY: self.kernel_version,
            models.PRIVATE_KEY: self.private,
            models.STATUS_KEY: self.status,
            models.VERSION_KEY: self.version
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
            local_obj = copy.deepcopy(json_obj)
            try:
                pop_f = local_obj.pop
                job = pop_f(models.JOB_KEY)
                kernel = pop_f(models.KERNEL_KEY)
                git_branch = pop_f(models.GIT_BRANCH_KEY)

                job_doc = JobDocument(job, kernel, git_branch)
                job_doc.id = pop_f(models.ID_KEY, None)

                for key, val in local_obj.iteritems():
                    setattr(job_doc, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                job_doc = None

        return job_doc
