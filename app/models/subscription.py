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

from models import BaseDocument

SUBSCRIPTION_COLLECTION = 'subscription'


class SubscriptionDocument(BaseDocument):

    def __init__(self, name):
        super(SubscriptionDocument, self).__init__(name)

    @staticmethod
    def from_json(json_obj):
        """Build a document from a JSON object.

        :param json_obj: The JSON object to start from.
        :return An instance of SubscriptionDocument.
        """
        name = json_obj.pop("_id")
        sub_doc = SubscriptionDocument(name)
        return sub_doc
