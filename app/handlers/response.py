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

"""A generic response object that handlers can pass along."""

from pymongo.cursor import Cursor
from types import (
    DictionaryType,
    IntType,
    ListType,
    StringTypes,
)


class HandlerResponse(object):
    """A custom response object that handlers should use to communicate.

    This has to be used to pass custom reason or set custom headers after
    an action has been performed.

    The result of the action must be stored in the object `result` attribute.
    This attribute will always be a list.

    `count` and `limit` should be stored in their own attributes as well.
    By default they are set to None and will not be included in the
    serializable view.

    To send this response on the wire, serialize the object by calling
    `to_dict()` or `repr`. They will return a dictionary view of the object.
    """
    def __init__(self, status_code=200):
        """Create a new HandlerResponse.

        By default the status code is set to 200.
        """
        if not isinstance(status_code, IntType):
            raise ValueError("Value must be an integer")

        self._status_code = status_code
        self._reason = None
        self._count = None
        self._limit = None
        self._result = []
        self._headers = {}

    @property
    def status_code(self):
        """The response status code."""
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        """The response status code.

        :param value: The status code, must be an int.
        """
        if not isinstance(value, IntType):
            raise ValueError("Value must be an integer")

        self._status_code = value

    @property
    def reason(self):
        """The response reason."""
        return self._reason

    @reason.setter
    def reason(self, value):
        """The response reason.

        :param value: The reason as string.
        """
        if not isinstance(value, StringTypes):
            raise ValueError("Value must be a string")

        self._reason = value

    @property
    def headers(self):
        """The custom headers for this response."""
        return self._headers

    @headers.setter
    def headers(self, value):
        """The headers that should be added to this response.

        :param value: A dictionary with the headers to set.
        """
        if not isinstance(value, DictionaryType):
            raise ValueError("Value must be a dictionary")

        self._headers = value

    @property
    def count(self):
        """How many result are included."""
        return self._count

    @count.setter
    def count(self, value):
        if not isinstance(value, IntType):
            raise ValueError("Value must be a integer")
        self._count = value

    @property
    def limit(self):
        """The number of result requested."""
        return self._limit

    @limit.setter
    def limit(self, value):
        if not isinstance(value, IntType):
            raise ValueError("Value must be an integer")
        self._limit = value

    @property
    def result(self):
        """The result associated with this response.

        :return A list containing the results or None if specifically set to.
        """
        return self._result

    @result.setter
    def result(self, value):
        """Set the result value.

        It can be set to None to control the `to_dict()` method and its output.
        If set to None, it will not be included in the dictionary view of the
        object.

        All passed values, if not of type list, will be wrapped around a list.
        """
        if value is None:
            self._result = value
        else:
            # The pymongo cursor is an iterable.
            if not isinstance(value, (ListType, Cursor)):
                value = [value]
            if isinstance(value, Cursor):
                value = [r for r in value]
            self._result = value

    def to_dict(self):
        """Create a view of this object as a dictionary.

        The `headers` property is not included.

        :return The object as a dictionary.
        """
        dict_obj = {}

        dict_obj['code'] = self.status_code
        if self.count is not None:
            dict_obj['count'] = self.count

        if self.limit is not None:
            dict_obj['limit'] = self.limit

        if self.result is not None:
            dict_obj['result'] = self.result

        if self.reason is not None:
            dict_obj['reason'] = self.reason

        return dict_obj

    def __repr__(self):
        return self.to_dict()
