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

"""Decorators used by handler methods."""

from functools import wraps

from models.token import TOKEN_COLLECTION
from utils.db import find_one

API_TOKEN_HEADER = 'X-Linaro-Token'


def protected(function):
    """Protects an HTTP method with token based auth/authz."""

    @wraps(function)
    def _func_wrapper(self, *args, **kwargs):
        token = self.request.headers.get(API_TOKEN_HEADER, None)

        if token and _is_valid_token(self, token):
            return function(self, *args, **kwargs)

        # If we get here, we have an error.
        self.log.info(
            "Token not authorized for IP address %s - Token: %s",
            self.request.remote_ip, token
        )
        self.send_error(403)

    return _func_wrapper


def _is_valid_token(self, token):
    """Check if a token is valid or not.

    :param self: This is the RequestHandler object as passed by the decorator.
    :param token: The token to check.
    :return True or False
    """
    is_valid = False

    self.log.debug(
        "Checking token %s from IP address", token, self.request.remote_ip
    )

    result = find_one(self.db[TOKEN_COLLECTION], [token], field='token')
    if result:
        is_valid = True

    return is_valid
