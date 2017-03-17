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

"""The model that represents the errors summary in the db."""

import types

import models
import models.base as modb


# Valid keys for API query parameters.
ERROR_SUMMARY_VALID_KEYS = {
    "GET": [
        models.CREATED_KEY,
        models.GIT_BRANCH_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY
    ]
}


class ErrorSummaryDocument(modb.BaseDocument):
    """Store the summary of extracted error values."""

    def __init__(self, job_id, version):
        self._created_on = None
        self._id = None
        self._version = version

        self.job_id = job_id

        self._errors = []
        self._mismatches = []
        self._warnings = []
        self.job = None
        self.kernel = None
        self.git_branch = None

    @property
    def collection(self):
        return models.ERRORS_SUMMARY_COLLECTION

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
        """The ID of this object as returned by the database."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the ID of this object with the ObjectID from the database.

        :param value: The ID of this object.
        :type value: ObjectID
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

        :param value: The error data structure to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._errors.extend(value)
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

        :param value: The warning data structure to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._warnings.extend(value)
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

        :param value: The mismatch data structure to store.
        :type value: list
        """
        if isinstance(value, types.ListType):
            self._mismatches.extend(value)
        else:
            raise TypeError(
                "Passed value for 'mismatches' is not a list: %s" %
                type(value))

    def to_dict(self):
        dict_obj = {
            models.CREATED_KEY: self.created_on,
            models.ERRORS_KEY: self.errors,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.MISMATCHES_KEY: self.mismatches,
            models.VERSION_KEY: self.version,
            models.WARNINGS_KEY: self.warnings
        }

        if self.id:
            dict_obj[models.ID_KEY] = self.id

        return dict_obj

    @staticmethod
    def from_json(json_obj):
        return None
