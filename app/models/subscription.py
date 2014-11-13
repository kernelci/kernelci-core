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

"""
The model that represents a subscription document in the mongodb collection.
"""

import types

import models
import models.base as modb


class SubscriptionDocument(modb.BaseDocument):
    """This class represents a subscription document in the mongodb database.

    A subscription document contains a list of emails that shoule be notified.
    It contains an external ID that points to the job ID.
    """

    def __init__(self, job, kernel):
        doc_name = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel
        }
        self._name = models.SUBSCRIPTION_DOCUMENT_NAME % doc_name
        self._created_on = None
        self._id = None
        self._job_id = None
        self._job = job
        self._kernel = kernel
        self._emails = []
        self._version = None

    @property
    def collection(self):
        return models.SUBSCRIPTION_COLLECTION

    @property
    def name(self):
        """The name of the object."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the document."""
        self._name = value

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
        """The real job name as found on the file system."""
        return self._job

    @property
    def kernel(self):
        """The real kernel name as found on the file system."""
        return self._kernel

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
    def job_id(self):
        """The job ID this subscriptions belong to."""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        """Set the ID of the associated job."""
        self._job_id = value

    @property
    def emails(self):
        """The list of emails subscribed."""
        return self._emails

    @emails.setter
    def emails(self, value):
        """Set the emails subscribed."""
        if not isinstance(value, types.ListType):
            if isinstance(value, types.StringTypes):
                value = [value]
            else:
                value = list(value)

        self._emails.extend(value)
        # Make sure the list is unique.
        self._emails = list(set(self._emails))

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
        sub_dict = {
            models.CREATED_KEY: self.created_on,
            models.EMAIL_LIST_KEY: self.emails,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.NAME_KEY: self.name,
            models.VERSION_KEY: self.version,
        }

        if self.id:
            sub_dict[models.ID_KEY] = self.id

        return sub_dict

    @staticmethod
    def from_json(json_obj):
        """Build a document from a JSON object.

        :param json_obj: The JSON object to start from.
        :return An instance of `SubscriptionDocument`.
        """
        sub_doc = None
        if isinstance(json_obj, types.DictionaryType):
            json_pop = json_obj.pop
            job = json_pop(models.JOB_KEY)
            kernel = json_pop(models.KERNEL_KEY)
            doc_id = json_pop(models.ID_KEY)
            # Remove the name key.
            json_pop(models.NAME_KEY)

            sub_doc = SubscriptionDocument(job, kernel)
            sub_doc.id = doc_id
            sub_doc.version = json_pop(models.VERSION_KEY, "1.0")

            for key, value in json_obj.iteritems():
                try:
                    setattr(sub_doc, key, value)
                except AttributeError:
                    print key

        return sub_doc
