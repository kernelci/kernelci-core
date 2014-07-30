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

from types import (
    DictionaryType,
    IntType,
    StringTypes,
)


class HandlerResponse(object):
    """A custom response object that handlers can use to communicate.

    This might be used to pass custom message or set custom headers after
    an action has been performed.
    """
    def __init__(self, status_code):
        if not isinstance(status_code, IntType):
            raise ValueError("Value must be an integer")

        self._status_code = status_code
        self._message = None
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
    def message(self):
        """The response message."""
        return self._message

    @message.setter
    def message(self, value):
        """The response message.

        :param value: The message as string.
        """
        if not isinstance(value, StringTypes):
            raise ValueError("Value must be a string")

        self._message = value

    @property
    def headers(self):
        """The custom headers for this response."""
        return self._headers

    @headers.setter
    def headers(self, value):
        """The headers for this response.

        :param value: A dictionary with the headers to set.
        """
        if not isinstance(value, DictionaryType):
            raise ValueError("Value must be a dictionary")

        self._headers = value
