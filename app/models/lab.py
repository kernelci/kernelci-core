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

"""The model that represents a lab for boot testing or other tests."""

import types

import models
import models.base as modb


class LabDocument(modb.BaseDocument):
    """This class represents a lab object as stored in the database.

    A lab object contains all the necessary information needed to set up and
    accepts data from external boot, test or whatever else labs.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name):
        self._name = name
        self._id = None
        self._created_on = None

        self._private = False
        self._address = {}
        self._contact = {}
        self._token = None
        self._updated_on = None

    @property
    def collection(self):
        return models.LAB_COLLECTION

    # pylint: disable=invalid-name
    @staticmethod
    def from_json(json_obj):
        lab_doc = None
        if json_obj:
            json_get = json_obj.get
            lab_doc = LabDocument(json_get(models.NAME_KEY))
            lab_doc.id = json_get(models.ID_KEY, None)
            lab_doc.created_on = json_get(models.CREATED_KEY)
            lab_doc.private = json_get(models.PRIVATE_KEY)
            lab_doc.address = json_get(models.ADDRESS_KEY)
            lab_doc.contact = json_get(models.CONTACT_KEY)
            lab_doc.token = json_get(models.TOKEN_KEY)
            lab_doc.updated_on = json_get(models.UPDATED_KEY)
        return lab_doc

    @property
    def name(self):
        """The name of the lab."""
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
    def private(self):
        """If this lab is private or not."""
        return self._private

    @private.setter
    def private(self, value):
        """Set whether this lab is private or not.

        :param value: If the lab is private or not.
        :type value: bool
        """
        self._private = value

    @property
    def address(self):
        """The address of this lab.

        :return A dictionary.
        """
        return self._address

    @address.setter
    def address(self, value):
        """Set the address of this lab.

        The address must be a dictionary containing the following keys:
         * street_1
         * street_2
         * city
         * country
         * zipcode
         * longitude
         * latitude

        Keys do not need to be all set, it is not mandatory to provide an
        address. Try to keep `street_1` and `street_2` under 64 chars: that's
        why two fields are provided.

        :param value: The address data structure for this lab.
        :type value: dict
        :raises TypeError if value is not a dict.
        """
        if not isinstance(value, types.DictType):
            raise TypeError("Passed value is not a dictionary")
        self._address = value

    @property
    def contact(self):
        """The contact details for this lab.

        :return A dictionary.
        """
        return self._contact

    @contact.setter
    def contact(self, value):
        """Set the contact for this lab.

        The contact must be a dictionary containing the following keys:
         * name
         * surname
         * telephone
         * mobile
         * email

        Mandatory keys are 'name', 'surname' and 'email'.

        :param value: The contact data structure for this lab.
        :type value: dict
        :raises TypeError if value is not a dict, ValueError if the mandatory
        fields are missing.
        """
        if not isinstance(value, types.DictType):
            raise TypeError("Passed value is not a dictionary")
        if not all(
            [value.get("name"), value.get("surname"), value.get("email")]
        ):
            raise ValueError(
                "Missing mandatory field (one of): name, surname or email"
            )
        self._contact = value

    @property
    def token(self):
        """The token ID associated with this lab."""
        return self._token

    @token.setter
    def token(self, value):
        """Set the token ID associated with this lab.

        This is not the real token value, just its ID as returned by mongodb.

        :param value: The ID of the token associated with the lab.
        :type value: str
        """
        self._token = value

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

    @property
    def updated_on(self):
        """When this lab object has been last updated."""
        return self._updated_on

    @updated_on.setter
    def updated_on(self, value):
        """Set the update date of this lab object.

        :param value: When this lab object has been update, in UTC time zone.
        :type value: datetime
        """
        self._updated_on = value

    def to_dict(self):
        """Create a serializable view of this document.

        :return A dictionary representation of the object.
        """
        lab_dict = {
            models.CREATED_KEY: self.created_on,
            models.UPDATED_KEY: self.updated_on,
            models.TOKEN_KEY: self.token,
            models.NAME_KEY: self.name,
            models.ADDRESS_KEY: self.address,
            models.CONTACT_KEY: self.contact,
            models.PRIVATE_KEY: self.private,
        }

        if self.id:
            lab_dict[models.ID_KEY] = self.id

        return lab_dict
