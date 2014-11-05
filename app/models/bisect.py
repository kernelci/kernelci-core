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

"""Bisect mongodb document models."""

import models
import models.base as modb


class BisectDocument(modb.BaseDocument):
    """The bisect document model class."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=invalid-name
    def __init__(self, name):
        self._name = name
        self._id = None
        self._job = None
        self._bisect_data = []
        self._bad_commit = None
        self._good_commit = None
        self._bad_commit_date = None
        self._good_commit_date = None
        self._bad_commit_url = None
        self._good_commit_url = None
        self._created_on = None

    @property
    def collection(self):
        """The name of this document collection.

        Where document of this kind will be stored.
        """
        return models.BISECT_COLLECTION

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
    def job(self):
        """The job this document is part of."""
        return self._job

    @job.setter
    def job(self, value):
        """Set the job this document is part of."""
        self._job = value

    @property
    def bad_commit_date(self):
        """The date of the bad commit."""
        return self._bad_commit_date

    @bad_commit_date.setter
    def bad_commit_date(self, value):
        """Set the date of the bad commit."""
        self._bad_commit_date = value

    @property
    def bad_commit(self):
        """The bad commit hash value."""
        return self._bad_commit

    @bad_commit.setter
    def bad_commit(self, value):
        """Set the bad commit hash value."""
        self._bad_commit = value

    @property
    def bad_commit_url(self):
        """The URL of the bad commit."""
        return self._bad_commit_url

    @bad_commit_url.setter
    def bad_commit_url(self, value):
        """Set the URL of the bad commit."""
        self._bad_commit_url = value

    @property
    def good_commit(self):
        """The good commit hash value."""
        return self._good_commit

    @good_commit.setter
    def good_commit(self, value):
        """Set the good commit hash value."""
        self._good_commit = value

    @property
    def good_commit_date(self):
        """The date of the good commit."""
        return self._good_commit_date

    @good_commit_date.setter
    def good_commit_date(self, value):
        """Set the date of the good commit."""
        self._good_commit_date = value

    @property
    def good_commit_url(self):
        """The URL of the good commit."""
        return self._good_commit_url

    @good_commit_url.setter
    def good_commit_url(self, value):
        """Set the URL of the good commit."""
        self._good_commit_url = value

    @property
    def bisect_data(self):
        """Get all the bisect data, ranging from the bad to the good commit."""
        return self._bisect_data

    @bisect_data.setter
    def bisect_data(self, value):
        """Set the bisect data."""
        self._bisect_data = value

    @property
    def created_on(self):
        """When this lab object was created."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this lab object.

        :param value: The lab creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

    def to_dict(self):
        bisect_dict = {
            models.CREATED_KEY: self.created_on,
            models.JOB_KEY: self.job,
            models.NAME_KEY: self.name,
            models.BISECT_DATA_KEY: self.bisect_data,
            models.BISECT_GOOD_COMMIT_KEY: self.good_commit,
            models.BISECT_GOOD_COMMIT_DATE: self.good_commit_date,
            models.BISECT_GOOD_COMMIT_URL: self.good_commit_url,
            models.BISECT_BAD_COMMIT_KEY: self.bad_commit,
            models.BISECT_BAD_COMMIT_DATE: self.bad_commit_date,
            models.BISECT_BAD_COMMIT_URL: self.bad_commit_url,
        }

        if self.id:
            bisect_dict[models.ID_KEY] = self.id

        return bisect_dict

    @staticmethod
    def from_json(json_obj):
        return None


class BootBisectDocument(BisectDocument):
    """The bisect document class for boot bisection."""

    def __init__(self, name):
        super(BootBisectDocument, self).__init__(name)

        self._board = None

    @property
    def board(self):
        """The board this document belongs to."""
        return self._board

    @board.setter
    def board(self, value):
        """Set the board name this document belongs to."""
        self._board = value

    def to_dict(self):
        boot_b_dict = super(BootBisectDocument, self).to_dict()
        boot_b_dict[models.BOARD_KEY] = self.board
        return boot_b_dict
