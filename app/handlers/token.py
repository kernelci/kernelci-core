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

import bson

from urlparse import urlunparse

from handlers.base import BaseHandler
from handlers.common import (
    NOT_VALID_TOKEN,
    TOKEN_VALID_KEYS,
    get_query_fields,
    valid_token_th,
    validate_token,
)
from handlers.response import HandlerResponse
from models import (
    ADMIN_KEY,
    DELETE_KEY,
    EMAIL_KEY,
    EXPIRES_KEY,
    GET_KEY,
    IP_ADDRESS_KEY,
    IP_RESTRICTED,
    POST_KEY,
    SUPERUSER_KEY,
    TOKEN_COLLECTION,
    TOKEN_KEY,
    USERNAME_KEY,
)
from models.token import Token
from utils.db import (
    delete,
    find_one,
    save,
    update,
)


class TokenHandler(BaseHandler):
    """Handle the /token URLs."""

    def __init__(self, application, request, **kwargs):
        super(TokenHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[TOKEN_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return TOKEN_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return valid_token_th

    def _token_validation(self, req_token, method, remote_ip, master_key):
        valid_token = False

        if all([master_key, req_token == master_key]):
            valid_token = True
        else:
            token_obj = self._find_token(req_token, self.db)

            if token_obj:
                valid_token = validate_token(
                    token_obj,
                    method,
                    remote_ip,
                    self._token_validation_func()
                )

        return valid_token

    def _get_one(self, doc_id):
        # Overridden: with the token we do not search by _id, but
        # by token field.
        response = HandlerResponse()
        response.result = None

        result = find_one(
            self.collection,
            doc_id,
            field=TOKEN_KEY,
            fields=get_query_fields(self.get_query_arguments)
        )

        if result:
            response.result = [result]
        else:
            response.status_code = 404
            response.reason = "Resource '%s' not found" % doc_id

        return response

    def _post(self, *args, **kwargs):
        response = None

        if kwargs and kwargs.get('id', None):
            self.log.info(
                "Token update from IP address %s",
                self.request.remote_ip
            )
            response = self._update_data(kwargs['id'], kwargs['json_obj'])
        else:
            self.log.info(
                "New token creation from IP address %s",
                self.request.remote_ip
            )
            response = self._new_data(kwargs['json_obj'])

        return response

    def _new_data(self, json_obj):
        """Create a new token in the DB.

        :param json_obj: The JSON object with the paramters.
        :return A `HandlerResponse` object.
        """
        response = HandlerResponse(201)
        response.result = None

        try:
            new_token = self._token_update_create(json_obj)

            response.status_code, _ = save(self.db, new_token)
            if response.status_code == 201:
                response.result = {TOKEN_KEY: new_token.token}
                location = urlunparse(
                    (
                        'http',
                        self.request.headers.get('Host'),
                        self.request.uri + '/' + new_token.token,
                        '', '', ''
                    )
                )
                response.headers = {'Location': location}
        except KeyError:
            response.status_code = 400
            response.reason = (
                "New tokens require the email address field [email]"
            )
        except (TypeError, ValueError):
            response.status_code = 400
            response.reason = "Wrong field value or type in the JSON data"
        except Exception, ex:
            response.status_code = 400
            response.reason = str(ex)

        return response

    def _update_data(self, doc_id, json_obj):
        """Update an existing `Token` in the DB.

        :param doc_id: The token string identifying the `Token` to update.
        :param json_obj: The JSON object with the parameters.
        :return A `HandlerResponse` objet.
        """
        response = HandlerResponse()
        response.result = None

        try:
            obj_id = bson.objectid.ObjectId(doc_id)
            result = find_one(self.collection, [obj_id])

            if result:
                token = Token.from_json(result)

                token = self._token_update_create(json_obj, token, fail=False)
                response.status_code = update(
                    self.collection, {'_id': obj_id}, token.to_dict()
                )
                if response.status_code == 200:
                    response.result = {TOKEN_KEY: token.token}
            else:
                response.status_code = 404
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Wrong ID '%s' value passed for object ID", doc_id)
            response.status_code = 400
            response.reason = "Wrong ID value provided"
        except KeyError, ex:
            self.log.exception(ex)
            response.status_code = 400
            response.reason = "Mandatory field missing"
        except (TypeError, ValueError), ex:
            self.log.exception(ex)
            response.status_code = 400
            response.reason = "Wrong field value or type in the JSON data"
        except Exception, ex:
            self.log.exception(ex)
            response.status_code = 400
            response.reason = str(ex)

        return response

    @staticmethod
    def _token_update_create(json_obj, token=None, fail=True):
        """Create or update a `Token` object.

        If the `token` argument is null, a new one will be created.

        :param json_obj: The JSON object with the values to update.
        :param token: The `Token` to update. Default to None meaning a new
            token will be created.
        param fail: If when a mandatory Token field is missing we should fail.
            By default True, and it fails when the `email` field is missing.
        :return A `Token`.
        :raise KeyError, ValueError, TypeError, Exception.
        """
        if not token:
            token = Token()

        if fail:
            token.email = json_obj[EMAIL_KEY]
        else:
            if json_obj.get(EMAIL_KEY, None):
                token.email = json_obj.get(EMAIL_KEY)

        if json_obj.get(USERNAME_KEY, None):
            token.username = json_obj.get(USERNAME_KEY)

        if json_obj.get(EXPIRES_KEY, None):
            token.expires_on = json_obj.get(EXPIRES_KEY)

        if json_obj.get(GET_KEY, None):
            token.is_get_token = json_obj.get(GET_KEY)

        if json_obj.get(POST_KEY, None):
            token.is_post_token = json_obj.get(POST_KEY)

        if json_obj.get(DELETE_KEY, None):
            token.is_delete_token = json_obj.get(DELETE_KEY)

        if json_obj.get(SUPERUSER_KEY, None):
            token.is_superuser = json_obj.get(SUPERUSER_KEY)

        if json_obj.get(ADMIN_KEY, None):
            token.is_admin = json_obj.get(ADMIN_KEY)

        if json_obj.get(IP_RESTRICTED, None):
            token.is_ip_restricted = json_obj.get(IP_RESTRICTED)

        if token.is_ip_restricted and not json_obj.get(IP_ADDRESS_KEY, None):
            raise Exception("IP restricted but no IP addresses given")
        elif json_obj.get(IP_ADDRESS_KEY, None) and not token.is_ip_restricted:
            raise Exception(
                "IP addresses given, but token is not IP restricted"
            )
        elif token.is_ip_restricted and json_obj.get(IP_ADDRESS_KEY, None):
            token.ip_address = json_obj.get(IP_ADDRESS_KEY)

        return token

    def execute_delete(self, *args, **kwargs):
        """Called by the actual DELETE method.

        Make sure we have the correct value to execute a DELETE on the db,
        and then call the method that does the real delete.

        Subclasses should not override this unless there are special reasons
        to.
        """
        response = HandlerResponse(400)

        if self.validate_req_token("DELETE"):
            if kwargs and kwargs.get('id', None):
                response.status_code = self._delete(kwargs['id'])
                if response.status_code == 200:
                    response.reason = "Resource deleted"
        else:
            response.status_code = 403
            response.reason = NOT_VALID_TOKEN

        return response

    def _delete(self, doc_id):
        ret_val = 404

        self.log.info("Token deletion from IP %s", self.request.remote_ip)
        try:
            doc_obj = bson.objectid.ObjectId(doc_id)
            if find_one(self.collection, [doc_obj]):
                ret_val = delete(self.collection, {"_id": {"$in": [doc_obj]}})
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Wrong ID '%s' value passed as object ID", doc_id)
            ret_val = 400

        return ret_val
