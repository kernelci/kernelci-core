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

"""The model that represents a defconfing document in the mongodb collection."""

import types

import models
import models.base as modb


# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
class DefconfigDocument(modb.BaseDocument):

    """This class represents a defconfig folder as seen on the file system."""

    def __init__(self, job, kernel, defconfig):

        doc_name = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.DEFCONFIG_KEY: defconfig
        }

        self._name = models.DEFCONFIG_DOCUMENT_NAME % doc_name
        self._id = None
        self._created_on = None

        self._job = job
        self._kernel = kernel
        self._defconfig = defconfig
        self._job_id = None
        self._dirname = None
        self._status = None
        self._metadata = {}
        self._errors = 0
        self._warnings = 0
        self._arch = None
        self._build_time = None

        self._git_url = None
        self._git_commit = None
        self._git_branch = None
        self._git_describe = None
        self._build_platform = []

    @property
    def collection(self):
        return models.DEFCONFIG_COLLECTION

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
    def job_id(self):
        """The job ID this defconfig belogns to."""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        """Set the job ID this defconfig belongs to.

        :param value: The job ID.
        :type value: str
        """
        self._job_id = value

    @property
    def job(self):
        """The job this defconfig belongs too."""
        return self._job

    @property
    def kernel(self):
        """The kernel this defconfig was built against."""
        return self._kernel

    @property
    def metadata(self):
        """A dictionary with metadata about this defconfig."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set the metadata about this defconfig.

        :param value: A dictionary with defconfig metadata.
        """
        if not isinstance(value, types.DictionaryType):
            raise TypeError(
                "Passed value is not a dictionary, got %s", type(value)
            )
        self._metadata = value

    @property
    def status(self):
        """The status of this defconfig built."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status.

        :param value: The status as string.
        """
        if value not in models.VALID_BUILD_STATUS:
            raise ValueError(
                "Status value '%s' not valid, should be one of: %s",
                value, str(models.VALID_BUILD_STATUS)
            )
        self._status = value

    @property
    def defconfig(self):
        """The defconfig name of this document."""
        return self._defconfig

    @property
    def errors(self):
        """Number of errors associated with this defconfig."""
        return self._errors

    @errors.setter
    def errors(self, value):
        """Set the number of errors."""
        self._errors = value

    @property
    def warnings(self):
        """Number of warnings associated with this defconfig."""
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        """Set the number of errors."""
        self._warnings = value

    @property
    def arch(self):
        """The architecture this defconfig has been built with."""
        return self._arch

    @arch.setter
    def arch(self, value):
        """Set the architecture this defconfig has been built with."""
        self._arch = value

    @property
    def dirname(self):
        """The name of the directory this defconfig is stored in."""
        return self._dirname

    @dirname.setter
    def dirname(self, value):
        """Set the name of the directory where this defconfig is stored."""
        self._dirname = value

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
    def build_platform(self):
        """Details about the platform used to build."""
        return self._build_platform

    @build_platform.setter
    def build_platform(self, value):
        """Set details about the build platform."""
        if not isinstance(value, types.ListType):
            raise TypeError("Value passed is not a list: %s", type(value))
        self._build_platform = value

    @property
    def git_describe(self):
        """The git describe value of the repository."""
        return self._git_describe

    @git_describe.setter
    def git_describe(self, value):
        """Set the git describe value of the repository."""
        self._git_describe = value

    @property
    def build_time(self):
        """How long it took to build this defconfig."""
        return self._build_time

    @build_time.setter
    def build_time(self, value):
        """Set the build time value."""
        self._build_time = value

    def to_dict(self):
        defconf_dict = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BUILD_PLATFORM_KEY: self.build_platform,
            models.BUILD_TIME_KEY: self.build_time,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DIRNAME_KEY: self.dirname,
            models.ERRORS_KEY: self.errors,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_URL_KEY: self.git_url,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.METADATA_KEY: self.metadata,
            models.NAME_KEY: self.name,
            models.STATUS_KEY: self.status,
            models.WARNINGS_KEY: self.warnings,
        }

        if self.id:
            defconf_dict[models.ID_KEY] = self.id

        return defconf_dict

    @staticmethod
    def from_json(json_obj):
        return None
