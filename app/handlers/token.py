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

import json
import tornado

from functools import partial
from tornado.web import (
    asynchronous,
)

from handlers.base import BaseHandler
from handlers.decorators import protected_th
from models import (
    ADMIN_KEY,
    CREATED_KEY,
    DELETE_KEY,
    EMAIL_KEY,
    EXPIRED_KEY,
    EXPIRES_KEY,
    GET_KEY,
    IP_ADDRESS_KEY,
    IP_RESTRICTED,
    POST_KEY,
    PROPERTIES_KEY,
    SUPERUSER_KEY,
    TOKEN_KEY,
    USERNAME_KEY,
)
from models.token import (
    TOKEN_COLLECTION,
    Token,
)
from utils.db import find_one
from utils.validator import is_valid_json


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
                ADMIN_KEY,
                DELETE_KEY,
                EMAIL_KEY,
                EXPIRES_KEY,
                GET_KEY,
                IP_ADDRESS_KEY,
                IP_RESTRICTED,
                POST_KEY,
                SUPERUSER_KEY,
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
        self.execute_get(*args, **kwargs)

    def _get_one(self, doc_id):
        # Overridden _get_one: with the token we do not search by _id, but
        # by token field.
        return find_one(
            self.collection, doc_id, field='token',
            fields=self._get_query_fields()
        )

    @protected_th("POST")
    @asynchronous
    def post(self, *args, **kwargs):
        self.executor.submit(
            partial(self._post, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(self._create_valid_response, future.result())
            )
        )

    def _post(self, *args, **kwargs):
        valid_request = self._valid_post_request()

        if valid_request == 200:
            try:
                json_obj = json.loads(self.request.body.decode('utf8'))

                if is_valid_json(json_obj, self._valid_keys('POST')):
                    if kwargs and kwargs.get('id', None):
                        self.log.info(
                            "New token creation from IP address %s",
                            self.request.remote_ip
                        )
                        return self._update_data(kwargs['id'], json_obj)
                    else:
                        self.log.info(
                            "Token update from IP address %s",
                            self.request.remote_ip
                        )
                        return self._new_data(json_obj)
                else:
                    self.write_error(
                        status_code=400,
                        message="Provided JSON is not valid"
                    )
            except ValueError:
                self.log.error("No JSON data found in the POST request")
                self.write_error(status_code=420)
        else:
            self.write_error(status_code=valid_request)

    def _new_data(self, json_obj):
        new_token = Token()

        try:
            new_token.email = json_obj[EMAIL_KEY]
            new_token.username = json_obj.get(USERNAME_KEY, None)
            new_token.expires_on = json_obj.get(EXPIRES_KEY, None)

            if json_obj.get(GET_KEY, None):
                new_token.is_get_token = json_obj.get(GET_KEY)

            if json_obj.get(POST_KEY, None):
                new_token.is_post_token = json_obj.get(POST_KEY)

            if json_obj.get(DELETE_KEY, None):
                new_token.is_delete_token = json_obj.get(DELETE_KEY)

            if json_obj.get(SUPERUSER_KEY, None):
                new_token.is_superuser = json_obj.get(SUPERUSER_KEY)

            if json_obj.get(ADMIN_KEY, None):
                new_token.is_admin = json_obj.get(ADMIN_KEY)

            new_token.is_ip_restricted = json_obj.get(IP_RESTRICTED, 0)
            if new_token.is_ip_restricted:
                if json_obj.get(IP_ADDRESS_KEY, None):
                    new_token.ip_address = json_obj.get(IP_ADDRESS_KEY, None)
                else:
                    raise Exception(
                        "IP restricted token but no IP addresses given"
                    )
        except KeyError:
            self.write_error(
                status_code=400,
                message="New tokens require the email address field [email]"
            )
        except (TypeError, ValueError):
            self.write_error(
                status_code=400,
                message="Wrong field value or type in the JSON data")
        except Exception, ex:
            self.write_error(
                status_code=400,
                message=str(ex)
            )
        else:
            return 201

    def _update_data(self, identifier, json_obj):
        return 202

    @protected_th("DELETE")
    @asynchronous
    def delete(self, *args, **kwargs):
        super(TokenHandler, self).delete(*args, **kwargs)

    def _delete(self, doc_id):
        pass
