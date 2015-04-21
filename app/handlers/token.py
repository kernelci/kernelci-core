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

try:
    import simplejson as json
except ImportError:
    import json

import bson
import urlparse

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import models.token as mtoken
import utils.db
import utils.validator as validator


# pylint: disable=too-many-public-methods
class TokenHandler(hbase.BaseHandler):
    """Handle the /token URLs."""

    def __init__(self, application, request, **kwargs):
        super(TokenHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.TOKEN_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return hcommon.TOKEN_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return hcommon.valid_token_th

    def _token_validation(self, req_token, method, remote_ip, master_key):
        valid_token = False
        token = None

        if all([master_key, req_token == master_key]):
            valid_token = True
        else:
            token_obj = self._find_token(req_token, self.db)

            if token_obj:
                valid_token, token = hcommon.validate_token(
                    token_obj,
                    method,
                    remote_ip,
                    self._token_validation_func()
                )

        return valid_token, token

    def _get_one(self, doc_id, **kwargs):
        # Overridden: with the token we do not search by _id, but
        # by token field.
        response = hresponse.HandlerResponse()

        result = utils.db.find_one2(
            self.collection,
            {models.TOKEN_KEY: doc_id},
            fields=hcommon.get_query_fields(self.get_query_arguments)
        )

        if result:
            response.result = [result]
        else:
            response.status_code = 404
            response.reason = "Resource '%s' not found" % doc_id

        return response

    def _post(self, *args, **kwargs):
        response = None

        if kwargs.get("id", None):
            response = hresponse.HandlerResponse(400)
            response.reason = "To update a token, use a PUT request"
        else:
            self.log.info(
                "New token creation from IP address %s",
                self.request.remote_ip)
            response = self._new_data(kwargs["json_obj"])

        return response

    def _put(self, *args, **kwargs):
        response = None

        # PUT and POST request require the same content type.
        valid_request = self._valid_post_request()
        if valid_request == 200:
            doc_id = kwargs.get("id", None)
            if doc_id:
                try:
                    json_obj = json.loads(self.request.body.decode("utf8"))

                    valid_json, errors = validator.is_valid_json(
                        json_obj, self._valid_keys("PUT"))
                    if valid_json:
                        response = self._update_data(doc_id, json_obj)
                        response.errors = errors
                    else:
                        response = hresponse.HandlerResponse(400)
                        response.reason = "Provided JSON is not valid"
                        response.errors = errors
                except ValueError, ex:
                    self.log.exception(ex)
                    error = "No JSON data found in the PUT request"
                    self.log.error(error)
                    response = hresponse.HandlerResponse(422)
                    response.reason = error
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "Missing token ID"
        else:
            response = hresponse.HandlerResponse(valid_request)
            response.reason = (
                "%s: %s" %
                (
                    self._get_status_message(valid_request),
                    "Use %s as the content type" % self.content_type
                )
            )

        return response

    def _new_data(self, json_obj):
        """Create a new token in the DB.

        :param json_obj: The JSON object with the paramters.
        :return A `HandlerResponse` object.
        """
        response = hresponse.HandlerResponse(201)

        try:
            new_token = self._token_update_create(json_obj)

            response.status_code, _ = utils.db.save(self.db, new_token)
            if response.status_code == 201:
                response.result = {models.TOKEN_KEY: new_token.token}
                location = urlparse.urlunparse(
                    (
                        "http",
                        self.request.headers.get("Host"),
                        self.request.uri + "/" + new_token.token,
                        "", "", ""
                    )
                )
                response.headers = {"Location": location}
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
        :type doc_id: string
        :param json_obj: The JSON object with the parameters.
        :type json_obj: dict
        :return A `HandlerResponse` object.
        """
        response = hresponse.HandlerResponse()

        try:
            token_oid = bson.objectid.ObjectId(doc_id)
            result = utils.db.find_one2(self.collection, token_oid)

            if result:
                token = mtoken.Token.from_json(result)

                token = self._token_update_create(json_obj, token, fail=False)
                response.status_code = utils.db.update(
                    self.collection,
                    {models.ID_KEY: token_oid},
                    token.to_dict()
                )
                if response.status_code == 200:
                    response.result = {models.TOKEN_KEY: token.token}
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

    # pylint: disable=too-many-branches
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
            token = mtoken.Token()

        json_get = json_obj.get

        if fail:
            token.email = json_obj[models.EMAIL_KEY]
        else:
            if json_get(models.EMAIL_KEY, None):
                token.email = json_get(models.EMAIL_KEY)

        if json_get(models.USERNAME_KEY, None):
            token.username = json_get(models.USERNAME_KEY)

        if json_get(models.EXPIRES_KEY, None):
            token.expires_on = json_get(models.EXPIRES_KEY)

        if str(json_get(models.EXPIRED_KEY, None)) != "None":
            token.expired = json_get(models.EXPIRED_KEY)

        if str(json_get(models.GET_KEY, None)) != "None":
            token.is_get_token = json_get(models.GET_KEY)

        if str(json_get(models.POST_KEY, None)) != "None":
            token.is_post_token = json_get(models.POST_KEY)

        if str(json_get(models.DELETE_KEY, None)) != "None":
            token.is_delete_token = json_get(models.DELETE_KEY)

        if str(json_get(models.SUPERUSER_KEY, None)) != "None":
            token.is_superuser = json_get(models.SUPERUSER_KEY)

        if str(json_get(models.ADMIN_KEY, None)) != "None":
            token.is_admin = json_get(models.ADMIN_KEY)

        if str(json_get(models.IP_RESTRICTED, None)) != "None":
            token.is_ip_restricted = json_get(models.IP_RESTRICTED)

        if str(json_get(models.LAB_KEY, None)) != "None":
            token.is_lab_token = json_get(models.LAB_KEY)

        if str(json_get(models.UPLOAD_KEY, None)) != "None":
            token.is_upload_token = json_get(models.UPLOAD_KEY)

        if str(json_get(models.TEST_LAB_KEY, None)) != "None":
            token.is_test_lab_token = json_get(models.TEST_LAB_KEY)

        if (token.is_ip_restricted and
                not json_get(models.IP_ADDRESS_KEY, None)):
            raise Exception("IP restricted but no IP addresses given")
        elif (json_get(models.IP_ADDRESS_KEY, None) and
                not token.is_ip_restricted):
            raise Exception(
                "IP addresses given, but token is not IP restricted"
            )
        elif token.is_ip_restricted and json_get(models.IP_ADDRESS_KEY, None):
            token.ip_address = json_get(models.IP_ADDRESS_KEY)

        return token

    def _delete(self, doc_id, **kwargs):
        """Delete a resource.

        :param doc_id: The ID of the resource to delete.
        :type doc_id: string
        :return The delete operation status code.
        """
        response = hresponse.HandlerResponse(200)

        try:
            token_oid = bson.objectid.ObjectId(doc_id)
            if utils.db.find_one2(self.collection, token_oid):
                self.log.info(
                    "Token (%s) deletion from IP '%s'",
                    doc_id, self.request.remote_ip)
                ret_val = utils.db.delete(self.collection, token_oid)
                response.status_code = ret_val

                if ret_val == 200:
                    response.reason = "Resource '%s' deleted" % doc_id
                else:
                    response.reason = "Error deleting resource '%s'" % doc_id
            else:
                response.status_code = 404
                response.reason = "Resource '%s' not found" % doc_id
        except bson.errors.InvalidId, ex:
            error = "Wrong ID value '%s' passed" % doc_id
            self.log.exception(ex)
            self.log.error(error)
            response.status_code = 400
            response.reason = error

        return response
