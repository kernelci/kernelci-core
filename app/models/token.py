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

"""The API token model to store token in the DB."""

import json

from bson import (
    json_util,
    tz_util,
)
from datetime import datetime
from netaddr import (
    IPAddress,
    IPNetwork,
    IPSet,
)
from netaddr.core import AddrFormatError
from types import (
    BooleanType,
    IntType,
    ListType,
    StringTypes,
)
from uuid import uuid4

from models import (
    CREATED_KEY,
    EMAIL_KEY,
    EXPIRED_KEY,
    EXPIRES_KEY,
    ID_KEY,
    IP_ADDRESS_KEY,
    PROPERTIES_KEY,
    TOKEN_COLLECTION,
    TOKEN_KEY,
    USERNAME_KEY,
)
from models.base import BaseDocument


class Token(BaseDocument):
    """This is an API token as stored in the DB.

    A token can be:
     - basic: All permissions have to be set (GET, POST, DELETE)
     - superuser: All methods are permitted, but cannot be used to create nor
        delete tokens.
     - admin: All operations permitted, can query, create and delete tokens.

    A token can be restricted to be used based on an IP address.

    Each token object has a properity called `properties`, a list of integers
    (0, 1) that describe the token. When the object is initialized, the list
    is all set to 0, and it has a default length of 16. Not all slots are used
    and will be left for future expansion.

    The property lists (index - property description) is as follows:
    - 0: if the token is an admin token
    - 1: if the token is a superuser token
    - 2: if the token can perform GET
    - 3: if the token can perfrom POST
    - 4: if the token can perform DELETE
    - 5: if the token is IP restricted
    - 6: if the token can create new tokens
    """

    def __init__(self):
        self._id = None
        self._token = None
        self._created_on = None
        self._expires_on = None
        self._expired = False
        self._username = None
        self._email = None
        self._ip_address = None
        self._properties = [0 for _ in range(0, 16)]

    @property
    def collection(self):
        return TOKEN_COLLECTION

    @property
    def token(self):
        if self._token is None:
            self._token = str(uuid4())

        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    @property
    def created_on(self):
        if not self._created_on:
            self._created_on = datetime.now(tz=tz_util.utc)
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        self._created_on = value

    @property
    def expires_on(self):
        return self._expires_on

    @expires_on.setter
    def expires_on(self, value):
        self._expires_on = self.check_expires_date(value)

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        if value is not None:
            if not isinstance(value, ListType):
                value = [value]
            value = self.check_ip_address(value)

        self._ip_address = value

    @property
    def expired(self):
        return self._expired

    @expired.setter
    def expired(self, value):
        self._expired = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def is_admin(self):
        return self._properties[0]

    @is_admin.setter
    def is_admin(self, value):
        value = self.check_attribute_value(value)

        self._properties[0] = value
        # Admin tokens can GET, POST and DELETE, are superuser and can create
        # new tokens.
        self._properties[1] = value
        self._properties[2] = value
        self._properties[3] = value
        self._properties[4] = value
        self._properties[6] = value

    @property
    def is_superuser(self):
        return self._properties[1]

    @is_superuser.setter
    def is_superuser(self, value):
        value = self.check_attribute_value(value)

        # Force admin to zero, and also if can create new tokens, regardless
        # of what is passed. A super user cannot create new tokens.
        self._properties[0] = 0
        self._properties[6] = 0

        self._properties[1] = value
        self._properties[2] = value
        self._properties[3] = value
        self._properties[4] = value

    @property
    def is_get_token(self):
        return self._properties[2]

    @is_get_token.setter
    def is_get_token(self, value):
        value = self.check_attribute_value(value)
        self._properties[2] = value

    @property
    def is_post_token(self):
        return self._properties[3]

    @is_post_token.setter
    def is_post_token(self, value):
        value = self.check_attribute_value(value)
        self._properties[3] = value

    @property
    def is_delete_token(self):
        return self._properties[4]

    @is_delete_token.setter
    def is_delete_token(self, value):
        value = self.check_attribute_value(value)
        self._properties[4] = value

    @property
    def is_ip_restricted(self):
        return self._properties[5]

    @is_ip_restricted.setter
    def is_ip_restricted(self, value):
        value = self.check_attribute_value(value)
        self._properties[5] = value

    @property
    def can_create_token(self):
        return self._properties[6]

    @can_create_token.setter
    def can_create_token(self, value):
        value = self.check_attribute_value(value)
        self._properties[6] = value

    def is_valid_ip(self, address):
        """Check if an IP address is valid for a token.

        :param address: The IP address to verify.
        :return True or False.
        """
        return_value = False

        if not self.is_ip_restricted:
            return_value = True
        else:
            try:
                address = self._convert_ip_address(address)
                if address in IPSet(self.ip_address):
                    return_value = True
            except AddrFormatError:
                # If we get an error converting the IP address, consider it
                # not valid and force False.
                return_value = False

        return return_value

    @classmethod
    def check_ip_address(cls, addrlist):
        """Perform sanity check and conversion on the IP address list.

        :return The address list converted with `IPaddress` and/or `IPNetwork`
            objects.
        """
        if not isinstance(addrlist, ListType):
            raise TypeError("Value must be a list of addresses")

        for idx, address in enumerate(addrlist):
            try:
                addrlist[idx] = cls._convert_ip_address(address)
            except AddrFormatError:
                raise ValueError(
                    "Address %s is not a valid IP address or network", address
                )
        return addrlist

    @staticmethod
    def _convert_ip_address(address):
        """Convert a string into an IPAddress or IPNetwork.

        :return An `IPAddress` or `IPNetwork` object.
        """
        if '/' in address:
            address = IPNetwork(address).ipv6(ipv4_compatible=True)
        else:
            address = IPAddress(address).ipv6(ipv4_compatible=True)
        return address

    @staticmethod
    def check_attribute_value(value):
        """Make sure the value passed for the properties list is valid.

        A properties value must be an integer or a boolean, either 0 or 1.
        Negative number will be converted into their absolute values.

        :param value: The value to check.
        :return The value converted into an int.
        :raise TypeError if the value is not IntType or BooleanType; ValueError
            if it is not 0 or 1.
        """
        if not isinstance(value, (IntType, BooleanType)):
            raise TypeError("Wrong value passed, must be int or bool")

        value = abs(int(value))
        if 0 != value != 1:
            raise ValueError("Value must be 0 or 1")

        return value

    @staticmethod
    def check_expires_date(value):
        """Check and convert the expiry date.

        Expiry date must follow this format: %Y-%m-%d.

        :param value: The date string.
        :return The converted date, or None if the passed value is None.
        :raise ValueError if the date string cannot be parsed accordingly to
            the predefined format.
        """
        try:
            if value:
                value = datetime.strptime(value, "%Y-%m-%d")
        except ValueError, ex:
            raise ex
        else:
            return value

    def to_dict(self):
        """Return a dictionary view of the object.

        :return The object as a dictionary.
        """
        doc_dict = {}
        doc_dict[CREATED_KEY] = self.created_on
        doc_dict[EMAIL_KEY] = self.email
        doc_dict[EXPIRED_KEY] = self.expired
        doc_dict[EXPIRES_KEY] = self.expires_on
        if self.ip_address is not None:
            doc_dict[IP_ADDRESS_KEY] = [str(x) for x in self.ip_address if x]
        else:
            doc_dict[IP_ADDRESS_KEY] = None
        doc_dict[PROPERTIES_KEY] = self.properties
        doc_dict[TOKEN_KEY] = self.token
        doc_dict[USERNAME_KEY] = self.username
        if self._id:
            doc_dict[ID_KEY] = self._id

        return doc_dict

    def to_json(self):
        """Return a JSON string for this object.

        :return A JSON string.
        """
        return json.dumps(self.to_dict(), default=json_util.default)

    @staticmethod
    def from_json(json_obj):
        """Build a Token object from a JSON string.

        :param json_obj: The JSON object to start from, or a JSON string.
        :return An instance of `Token`.
        """
        if isinstance(json_obj, StringTypes):
            json_obj = json_util.loads(json_obj)

        token = Token()
        for key, value in json_obj.iteritems():
            setattr(token, key, value)

        return token
