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

from models import (
    BISECT_BAD_COMMIT_DATE,
    BISECT_BAD_COMMIT_KEY,
    BISECT_BAD_COMMIT_URL,
    BISECT_COLLECTION,
    BISECT_DATA_KEY,
    BISECT_GOOD_COMMIT_DATE,
    BISECT_GOOD_COMMIT_KEY,
    BISECT_GOOD_COMMIT_URL,
    BOARD_KEY,
    CREATED_KEY,
    DOC_ID_KEY,
    ID_KEY,
    JOB_KEY,
)
from models.base import BaseDocument


class BisectDocument(BaseDocument):
    """The bisect document model class."""

    def __init__(self, name):
        super(BisectDocument, self).__init__(name)

        self._id = None
        self._job = None
        self._bisect_data = []
        self._bad_commit = None
        self._good_commit = None
        self._bad_commit_date = None
        self._good_commit_date = None
        self._bad_commit_url = None
        self._good_commit_url = None

    @property
    def collection(self):
        """The name of this document collection.

        Where document of this kind will be stored.
        """
        return BISECT_COLLECTION

    @property
    def id(self):
        """The ID of this object in the database.

        This value should be returned by mongodb.
        """
        return self._id

    @property
    def doc_id(self):
        """The interl doc ID."""
        return self._name

    @id.setter
    def id(self, value):
        """Set the ID of this object."""
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

    def to_dict(self):
        bisect_dict = {
            CREATED_KEY: self._created_on,
            JOB_KEY: self._job,
            DOC_ID_KEY: self._name,
            BISECT_DATA_KEY: self._bisect_data,
            BISECT_GOOD_COMMIT_KEY: self._good_commit,
            BISECT_GOOD_COMMIT_DATE: self._good_commit_date,
            BISECT_GOOD_COMMIT_URL: self._good_commit_url,
            BISECT_BAD_COMMIT_KEY: self._bad_commit,
            BISECT_BAD_COMMIT_DATE: self._bad_commit_date,
            BISECT_BAD_COMMIT_URL: self._bad_commit_url,
        }

        if self._id:
            bisect_dict[ID_KEY] = self._id

        return bisect_dict


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
        boot_b_dict[BOARD_KEY] = self._board
        return boot_b_dict
