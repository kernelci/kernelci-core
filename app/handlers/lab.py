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

"""Handler for the /lab URLs."""

try:
    import simplejson as json
except ImportError:
    import json

import bson

import handlers.base
import handlers.common.lab
import handlers.common.query
import handlers.common.token
import handlers.response as hresponse
import models
import utils.db
import utils.validator as validator


# pylint: disable=too-many-public-methods
class LabHandler(handlers.base.BaseHandler):
    """Handle all traffic through the /lab URLs."""

    def __init__(self, application, request, **kwargs):
        super(LabHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.LAB_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.LAB_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return handlers.common.token.valid_token_th

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(201)
        if kwargs.get("id", None):
            response.status_code = 400
            response.reason = "To update a lab, perform a PUT request"
        else:
            json_obj = kwargs["json_obj"]

            valid_contact, reason = \
                validator.is_valid_lab_contact_data(json_obj)

            if valid_contact:
                response = handlers.common.lab.create_lab(
                    json_obj, self.db, self.request.uri)
            else:
                response.status_code = 400
                if reason:
                    response.reason = reason

        return response

    def _put(self, *args, **kwargs):
        response = None

        # PUT and POST request require the same content type.
        valid_request = handlers.common.request.valid_post_request(
            self.request.headers, self.request.remote_ip)

        if valid_request == 200:
            doc_id = kwargs.get("id", None)
            if all([doc_id, validator.is_valid_id(doc_id)]):
                try:
                    json_obj = json.loads(self.request.body.decode("utf8"))

                    valid_json, errors = validator.is_valid_json(
                        json_obj, self._valid_keys("PUT"))

                    if valid_json:
                        response = handlers.common.lab.update_lab(
                            doc_id, json_obj, self._valid_keys("PUT"), self.db)
                    else:
                        response = hresponse.HandlerResponse(400)
                        response.reason = "Provided JSON is not valid"

                    response.errors = errors
                except ValueError:
                    error = "No JSON data found in the PUT request"
                    self.log.error(error)
                    response = hresponse.HandlerResponse(422)
                    response.reason = error
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "Wrong or missing lab ID"
        else:
            response = hresponse.HandlerResponse(valid_request)
            response.reason = \
                "Wrong content type, must be '%s'" % self.content_type

        return response

    def execute_delete(self, *args, **kwargs):
        response = None
        valid_token, _ = self.validate_req_token("DELETE")

        if valid_token:
            lab_id = kwargs.get("id", None)

            if all([lab_id, validator.is_valid_id(lab_id)]):
                lab_bson_id = bson.objectid.ObjectId(lab_id)

                lab_doc = utils.db.find_one2(
                    self.collection, {models.ID_KEY: lab_bson_id})

                if lab_doc:
                    token_id = lab_doc.get(models.TOKEN_KEY, None)
                    response = self._delete(
                        {models.ID_KEY: lab_bson_id}, token_id=token_id)

                    if response.status_code == 500:
                        response.reason = \
                            "Error deleting resource '%s'" % lab_id
                    else:
                        response.reason = "Resource '%s' deleted" % lab_id
                else:
                    response = hresponse.HandlerResponse(404)
                    response.reason = "Resource '%s' not found" % lab_id
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "Wrong or missing lab ID"
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _delete(self, spec_or_id, **kwargs):
        response = hresponse.HandlerResponse(200)
        ret_val = 200

        token_id = kwargs.get("token_id", None)

        ret_val = utils.db.delete(self.collection, spec_or_id)
        if all([ret_val != 500, token_id]):
            token_ret_val = utils.db.delete(
                self.db[models.TOKEN_COLLECTION],
                {models.ID_KEY: token_id})
            if token_ret_val == 500:
                response.errors = "Error deleting/disabling associated token"

        response.status_code = ret_val

        return response
