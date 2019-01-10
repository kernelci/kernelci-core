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

"""The model that represents an error logs document in the db."""

import types

import models
import models.base as modb


# Valid keys for API query parameters.
ERROR_LOG_VALID_KEYS = {
    "GET": [
        models.ARCHITECTURE_KEY,
        models.BUILD_ID_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_KEY,
        models.ERRORS_COUNT_KEY,
        models.GIT_BRANCH_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.MISMATCHES_COUNT_KEY,
        models.STATUS_KEY,
        models.VERSION_KEY,
        models.WARNINGS_COUNT_KEY
    ]
}


class ErrorLogDocument(modb.BaseDocument):
    """Store log errors, warnings and other extracted values."""

    def __init__(self, job_id, version):
        self._created_on = None
        self._id = None
        self._version = version

        self.job_id = job_id

        self._errors = []
        self._errors_count = 0
        self._mismatches = []
        self._mismatches_count = 0
        self._warnings = []
        self._warnings_count = 0
        self.arch = None
        self.build_environment = None
        self.build_id = None
        self.compiler = None
        self.compiler_version = None
        self.compiler_version_ext = None
        self.compiler_version_full = None
        self.defconfig = None
        self.defconfig_full = None
        self.file_server_resource = None
        self.file_server_url = None
        self.git_branch = None
        self.job = None
        self.kernel = None
        self.status = None

    @property
    def collection(self):
        return models.ERROR_LOGS_COLLECTION

    @property
    def created_on(self):
        """When this object was created."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this object.

        :param value: The document creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

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
    def version(self):
        """The version of the document schema."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the version of the document schema."""
        self._version = value

    @property
    def errors(self):
        """The error strings."""
        return self._errors

    @errors.setter
    def errors(self, value):
        """Set the error strings.

        :param value: The error strings to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._errors = value
        else:
            raise TypeError(
                "Passed value for 'errors' is not a list: %s" % type(value))

    @property
    def warnings(self):
        """The warning strings."""
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        """Set the warning strings.

        :param value: The warning strings to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._warnings = value
        else:
            raise TypeError(
                "Passed value for 'warnings' is not a list: %s" % type(value))

    @property
    def mismatches(self):
        """The mismatch strings."""
        return self._mismatches

    @mismatches.setter
    def mismatches(self, value):
        """Set the mismatch strings.

        :param value: The mismatch strings to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._mismatches = value
        else:
            raise TypeError(
                "Passed value for 'mismatches' is not a list: %s" %
                type(value))

    @property
    def errors_count(self):
        """Get the number or error lines."""
        return self._errors_count

    @errors_count.setter
    def errors_count(self, value):
        """Set the number of error lines.

        :param value: The number of lines.
        :type value: integer
        """
        self._errors_count = value

    @property
    def warnings_count(self):
        """Get the number of warning lines."""
        return self._warnings_count

    @warnings_count.setter
    def warnings_count(self, value):
        """Set the number of warning lines.

        :param value: The number of lines.
        :type values: integer
        """
        self._warnings_count = value

    @property
    def mismatches_count(self):
        """Get the number of mismatched lines."""
        return self._mismatches_count

    @mismatches_count.setter
    def mismatches_count(self, value):
        """Set the number of mismatched lines.

        :param value: The number of lines.
        :type values: integer
        """
        self._mismatches_count = value

    def to_dict(self):
        err_log = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BUILD_ENVIRONMENT_KEY: self.build_environment,
            models.BUILD_ID_KEY: self.build_id,
            models.COMPILER_KEY: self.compiler,
            models.COMPILER_VERSION_EXT_KEY: self.compiler_version_ext,
            models.COMPILER_VERSION_FULL_KEY: self.compiler_version_full,
            models.COMPILER_VERSION_KEY: self.compiler_version,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full,
            models.DEFCONFIG_KEY: self.defconfig,
            models.ERRORS_COUNT_KEY: self.errors_count,
            models.ERRORS_KEY: self.errors,
            models.FILE_SERVER_RESOURCE_KEY: self.file_server_resource,
            models.FILE_SERVER_URL_KEY: self.file_server_url,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.MISMATCHES_COUNT_KEY: self.mismatches_count,
            models.MISMATCHES_KEY: self.mismatches,
            models.STATUS_KEY: self.status,
            models.VERSION_KEY: self.version,
            models.WARNINGS_COUNT_KEY: self.warnings_count,
            models.WARNINGS_KEY: self.warnings
        }

        if self.id:
            err_log[models.ID_KEY] = self.id

        return err_log

    @staticmethod
    def from_json(json_obj):
        return None
