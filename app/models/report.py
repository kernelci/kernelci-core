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

"""The model that represents a report document to store in the db.

Reports here refer to boot or build email reports as sent (or not sent).
"""

import bson
import copy
import datetime
import types

import models
import models.base as modb


# pylint: disable=too-many-instance-attributes
class ReportDocument(modb.BaseDocument):
    """A report document that should be stored in the db.

    This is used to provide some historic data about email reports sent or
    which error they had when sending.
    """
    def __init__(self, name, version="1.0"):
        self._created_on = None
        self._id = None
        self._name = name
        self._version = version

        self.errors = []
        self.job = None
        self.kernel = None
        # The report type.
        self.r_type = None
        self.status = None
        self.updated_on = None

    @property
    def collection(self):
        return models.REPORT_COLLECTION

    @property
    def name(self):
        """The name of the report."""
        return self._name

    # pylint: disable=invalid-name
    @property
    def id(self):
        """The ID of this object as returned by mongodb."""
        return self._id

    # pylint: disable=invalid-name
    @id.setter
    def id(self, value):
        """Set the ID of this object with the ObjectID from mongodb.

        :param value: The ID of this object.
        :type value: str
        """
        self._id = value

    @property
    def version(self):
        """The schema version of this document."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this document."""
        self._version = value

    @property
    def created_on(self):
        """When this object was created."""
        if self._created_on is None:
            self._created_on = datetime.datetime.now(tz=bson.tz_util.utc)
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this lab object.

        :param value: The lab creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

    def to_dict(self):
        report_dict = {
            models.CREATED_KEY: self.created_on,
            models.ERRORS_KEY: self.errors,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.NAME_KEY: self.name,
            models.STATUS_KEY: self.status,
            models.TYPE_KEY: self.r_type,
            models.UPDATED_KEY: self.updated_on,
            models.VERSION_KEY: self.version
        }

        if self.id:
            report_dict[models.ID_KEY] = self.id

        return report_dict

    @staticmethod
    def from_json(json_obj):
        report_doc = None

        if json_obj and isinstance(json_obj, types.DictionaryType):
            local_obj = copy.deepcopy(json_obj)
            j_pop = local_obj.pop

            report_doc = ReportDocument(
                j_pop(models.NAME_KEY), version=j_pop(models.VERSION_KEY))

            report_doc.r_type = j_pop(models.TYPE_KEY)

            for key, val in local_obj.iteritems():
                setattr(report_doc, key, val)

            report_doc.updated_on = datetime.datetime.now(tz=bson.tz_util.utc)

        return report_doc
