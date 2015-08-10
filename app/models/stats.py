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

"""Document/Schema for the calculated statistics."""

import bson
import datetime

import models
import models.base as mbase


# pylint: disable=too-many-instance-attributes
class DailyStats(mbase.BaseDocument):
    """A document for the daily calculated statistics.

    Daily statistics cover all the database collections and include:
    - Actual count of documents in the collections
    - Count of documents in the collections from the previous day
    - Count of documents in the collections from the previous 7 days
    - Count of documents in the collections from the previous 14 days
    """

    def __init__(self, version="1.0"):
        self._created_on = None
        self._id = None
        self._version = version

        self.total_boots = 0
        self.total_builds = 0
        self.total_jobs = 0

        self.total_unique_trees = 0
        self.total_unique_kernels = 0
        self.total_unique_defconfigs = 0

        self.total_unique_boards = 0
        self.total_unique_machs = 0
        self.total_unique_archs = 0

        self.daily_total_boots = 0
        self.daily_total_builds = 0
        self.daily_total_jobs = 0

        self.daily_unique_boards = 0
        self.daily_unique_machs = 0
        self.daily_unique_archs = 0

        self.daily_unique_trees = 0
        self.daily_unique_kernels = 0
        self.daily_unique_defconfigs = 0

        self.weekly_total_boots = 0
        self.weekly_total_builds = 0
        self.weekly_total_jobs = 0

        self.weekly_unique_trees = 0
        self.weekly_unique_kernels = 0
        self.weekly_unique_defconfigs = 0

        self.weekly_unique_boards = 0
        self.weekly_unique_machs = 0
        self.weekly_unique_archs = 0

        self.biweekly_total_boots = 0
        self.biweekly_total_builds = 0
        self.biweekly_total_jobs = 0

        self.biweekly_unique_boards = 0
        self.biweekly_unique_machs = 0
        self.biweekly_unique_archs = 0

        self.biweekly_unique_trees = 0
        self.biweekly_unique_kernels = 0
        self.biweekly_unique_defconfigs = 0

    @property
    def collection(self):
        return models.DAILY_STATS_COLLECTION

    # pylint: disable=invalid-name
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
        """When this lab object was created."""
        if not self._created_on:
            self._created_on = datetime.datetime.now(tz=bson.tz_util.utc)
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this lab object.

        :param value: The lab creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

    @property
    def version(self):
        """The version of this document schema."""
        return self._version

    @version.setter
    def version(self, value):
        """The version of this document schema."""
        self._version = value

    def to_dict(self):
        """Create a dictionary for the object."""
        daily_stats = {
            models.CREATED_KEY: self.created_on,
            models.VERSION_KEY: self.version,
            "biweekly_total_boots": self.biweekly_total_boots,
            "biweekly_total_builds": self.biweekly_total_builds,
            "biweekly_total_jobs": self.biweekly_total_jobs,
            "biweekly_unique_archs": self.biweekly_unique_archs,
            "biweekly_unique_boards": self.biweekly_unique_boards,
            "biweekly_unique_kernels": self.biweekly_unique_kernels,
            "biweekly_unique_machs": self.biweekly_unique_machs,
            "biweekly_unique_trees": self.biweekly_unique_trees,
            "biweekly_unique_defconfigs": self.biweekly_unique_defconfigs,
            "daily_total_boots": self.daily_total_boots,
            "daily_total_builds": self.daily_total_builds,
            "daily_total_jobs": self.daily_total_jobs,
            "daily_unique_archs": self.daily_unique_archs,
            "daily_unique_boards": self.daily_unique_boards,
            "daily_unique_kernels": self.daily_unique_kernels,
            "daily_unique_machs": self.daily_unique_machs,
            "daily_unique_trees": self.daily_unique_trees,
            "daily_unique_defconfigs": self.daily_unique_defconfigs,
            "total_boots": self.total_boots,
            "total_builds": self.total_builds,
            "total_jobs": self.total_jobs,
            "total_unique_archs": self.total_unique_archs,
            "total_unique_boards": self.total_unique_boards,
            "total_unique_kernels": self.total_unique_kernels,
            "total_unique_machs": self.total_unique_machs,
            "total_unique_trees": self.total_unique_trees,
            "total_unique_defconfigs": self.total_unique_defconfigs,
            "weekly_total_boots": self.weekly_total_boots,
            "weekly_total_builds": self.weekly_total_builds,
            "weekly_total_jobs": self.weekly_total_jobs,
            "weekly_unique_archs": self.weekly_unique_archs,
            "weekly_unique_boards": self.weekly_unique_boards,
            "weekly_unique_kernels": self.weekly_unique_kernels,
            "weekly_unique_machs": self.weekly_unique_machs,
            "weekly_unique_trees": self.weekly_unique_trees,
            "weekly_unique_defconfigs": self.weekly_unique_defconfigs
        }

        if self.id:
            daily_stats[models.ID_KEY] = self.id

        return daily_stats

    @staticmethod
    def from_json(json_obj):
        """Create an object from JSON data."""
        return None
