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

"""The RequestHandler for /token URLs."""

from tornado.web import (
    asynchronous,
)

from handlers.base import BaseHandler
from handlers.decorators import protected_th
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
from models.token import TOKEN_COLLECTION


class TokenHandler(BaseHandler):
    """Handle the /job URLs."""

    def __init__(self, application, request, **kwargs):
        super(TokenHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[TOKEN_COLLECTION]

    def _valid_keys(self, method):
        valid_keys = {
            'POST': [
                EMAIL_KEY,
                EXPIRES_KEY,
                IP_ADDRESS_KEY,
                USERNAME_KEY,
            ],
            'GET': [
                CREATED_KEY,
                EMAIL_KEY,
                EXPIRED_KEY,
                EXPIRES_KEY,
                IP_ADDRESS_KEY,
                PROPERTIES_KEY,
                TOKEN_KEY,
                USERNAME_KEY,
            ],
        }

        return valid_keys.get(method, None)

    @protected_th("GET")
    @asynchronous
    def get(self, *args, **kwargs):
        super(TokenHandler, self).get(*args, **kwargs)
