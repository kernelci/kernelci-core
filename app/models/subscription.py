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

"""
The model that represents a subscription document in the mongodb collection.
"""

import types

from models import ID_KEY
from models.base import BaseDocument

SUBSCRIPTION_COLLECTION = 'subscription'


class SubscriptionDocument(BaseDocument):
    """This class represents a subscription document in the mongodb database.

    A subscription document contains a list of emails that shoule be notified.
    It contains an external ID that points to the job ID.
    """

    SUBSCRIPTION_ID_FORMAT = 'sub-%s'

    def __init__(self, name, job_id, emails=None):
        super(SubscriptionDocument, self).__init__(name)
        self._job_id = job_id
        self._emails = [] if emails is None else emails

    @property
    def collection(self):
        return SUBSCRIPTION_COLLECTION

    @property
    def job_id(self):
        """The job ID this subscriptions belong to."""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        """Set the job ID."""
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

    def to_dict(self):
        sub_dict = super(SubscriptionDocument, self).to_dict()
        sub_dict['emails'] = self._emails
        sub_dict['job_id'] = self._job_id
        return sub_dict

    @staticmethod
    def from_json(json_obj):
        """Build a document from a JSON object.

        :param json_obj: The JSON object to start from.
        :return An instance of SubscriptionDocument.
        """
        sub_doc = SubscriptionDocument(
            json_obj[ID_KEY],
            json_obj['job_id'],
            json_obj['emails']
        )
        return sub_doc
