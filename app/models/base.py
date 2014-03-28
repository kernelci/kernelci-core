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

"""The base document model that represents a mongodb document."""

import json

from models import ID_KEY


class BaseDocument(object):
    """The base document model for all other documents."""

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        """The name of this document.

        It should be used as the `_id' field in a mongodb document.
        """
        return self._name

    @property
    def collection(self):
        """The collection this document should belong to.

        :return None, subclasses should implement it.
        """
        return None

    def __repr__(self):
        return self.to_json()

    def to_dict(self):
        """Return a dictionary view of the document.

        The name attribute will be available as the `_id' key, useful for
        mongodb document.

        :return A dictionary.
        """
        return {
            ID_KEY: self._name
        }

    def to_json(self):
        """Return a JSON string for this object.

        :return A JSON string.
        """
        return json.dumps(self.to_dict())
