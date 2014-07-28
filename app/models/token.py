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

TOKEN_COLLECTION = 'api-token'

import json

from bson import json_util
from datetime import datetime
from types import (
    IntType,
    BooleanType,
)
from uuid import uuid4

from models import (
    CREATED_KEY,
    EMAIL_KEY,
    EXPIRED_KEY,
    EXPIRES_KEY,
    IP_ADDRESS_KEY,
    PROPERTIES_KEY,
    TOKEN_KEY,
    USERNAME_KEY,
)


class Token(object):
    """This is an API token as stored on the DB.

    A token can be:
     - basic: All permissions have to be set (GET, POST, DELETE)
     - superuser: All methods are permitted, but cannot be used to create new
        tokens
     - admin: All operations permitted, can create new tokens.

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
        self._token = str(uuid4())
        self._created_on = datetime.now()
        self._expires_on = None
        self._expired = False
        self._username = None
        self._email = None
        self._ip_address = None
        self._properties = [0 for _ in range(0, 16)]

    @property
    def token(self):
        return self._token

    @property
    def properties(self):
        return self._properties

    @property
    def created_on(self):
        return self._created_on

    @property
    def expires_on(self):
        return self._expires_on

    @expires_on.setter
    def expires_on(self, value):
        self._expires_on = value

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        # TODO: need IP address checking logic
        # use netaddr (0.7.2) for py 2.7, py >3.3 is part of the stdlib
        self._ip_address = value

    @property
    def expired(self):
        return self._expired

    @expired.setter
    def expired(self, value):
        self._expired = value

    @property
    def is_admin(self):
        return self._properties[0]

    @is_admin.setter
    def is_admin(self, value):
        value = self._check_properties_value(value)

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
        value = self._check_properties_value(value)

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
        value = self._check_properties_value(value)
        self._properties[2] = value

    @property
    def is_post_token(self):
        return self._properties[3]

    @is_post_token.setter
    def is_post_token(self, value):
        value = self._check_properties_value(value)
        self._properties[3] = value

    @property
    def is_delete_token(self):
        return self._properties[4]

    @is_delete_token.setter
    def is_delete_token(self, value):
        value = self._check_properties_value(value)
        self._properties[4] = value

    @property
    def is_ip_restricted(self):
        return self._properties[5]

    @is_ip_restricted.setter
    def is_ip_restricted(self, value):
        value = self._check_properties_value(value)
        self._properties[5] = value

    @property
    def can_create_token(self):
        return self._properties[6]

    @can_create_token.setter
    def can_create_token(self, value):
        value = self._check_properties_value(value)
        self._properties[6] = value

    @staticmethod
    def _check_properties_value(value):
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

    def to_dict(self):
        """Return a dictionary view of the object.

        :return The object as a dictionary.
        """
        return {
            CREATED_KEY: self._created_on,
            EMAIL_KEY: self._email,
            EXPIRED_KEY: self._expired,
            EXPIRES_KEY: self._expires_on,
            IP_ADDRESS_KEY: self._ip_address,
            PROPERTIES_KEY: self._properties,
            TOKEN_KEY: self._token,
            USERNAME_KEY: self._username,
        }

    def to_json(self):
        """Return a JSON string for this object.

        :return A JSON string.
        """
        return json.dumps(self.to_dict(), default=json_util.default)
