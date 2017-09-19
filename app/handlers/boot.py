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

"""The RequestHandler for /boot URLs."""

import bson

import handlers.base as hbase
import handlers.common.query
import handlers.common.token
import handlers.response as hresponse
import models
import models.lab as mlab
import models.token as mtoken
import taskqueue.tasks
import taskqueue.tasks.boot as taskq
import utils.db


class BootHandler(hbase.BaseHandler):
    """Handle the /boot URLs."""

    def __init__(self, application, request, **kwargs):
        super(BootHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.BOOT_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.BOOT_VALID_KEYS.get(method, None)

    @staticmethod
    def _token_validation_func():
        return handlers.common.token.valid_token_bh

    def _post(self, *args, **kwargs):
        lab_name = kwargs["json_obj"].get(models.LAB_NAME_KEY, None)
        req_token = kwargs["token"]

        valid_lab, error = self._is_valid_token(req_token, lab_name)
        if valid_lab:
            response = hresponse.HandlerResponse(202)
            response.reason = "Request accepted and being imported"

            taskq.import_boot.apply_async(
                [kwargs["json_obj"]],
                link=taskq.find_regression.s(),
                link_error=taskqueue.tasks.error_handler.s()
            )
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = (
                "Provided authentication token is not associated with "
                "lab '%s' or is not valid" % lab_name)

        response.errors = error

        return response

    def _is_valid_token(self, req_token, lab_name):
        """Make sure the token used to perform the POST is valid.

        We are being paranoid here. We need to make sure the token used to
        post is really associated with the provided lab name.

        To be valid to post boot report, the token must either be an admin
        token or a valid token associated with the lab.

        :param req_token: The token string from the request.
        :type req_token: str
        :param lab_name: The name of the lab to check.
        :type lab_name: str
        :return True if the token is valid, False otherwise.
        """
        valid_lab = False
        error = None

        lab_doc = utils.db.find_one2(
            self.db[models.LAB_COLLECTION], {models.NAME_KEY: lab_name})

        if lab_doc:
            lab_token_doc = utils.db.find_one2(
                self.db[models.TOKEN_COLLECTION], lab_doc[models.TOKEN_KEY])

            if lab_token_doc:
                lab_token = mtoken.Token.from_json(lab_token_doc)
                if req_token.is_admin:
                    valid_lab = True
                    self.log.warn(
                        "Received boot POST request from an admin token")
                    error = (
                        "Using an admin token to send boot reports: "
                        "use the lab token")
                elif (req_token.token == lab_token.token and
                        not lab_token.expired):
                    valid_lab = True
                else:
                    self.log.warn(
                        "Provided token (%s) is not associated with "
                        "lab '%s' or is not valid",
                        req_token, lab_name
                    )

        return valid_lab, error

    def execute_delete(self, *args, **kwargs):
        response = None
        valid_token, token = self.validate_req_token("DELETE")

        if valid_token:
            if kwargs and kwargs.get("id", None):
                try:
                    doc_id = kwargs["id"]
                    obj_id = bson.objectid.ObjectId(doc_id)

                    boot_doc = utils.db.find_one2(self.collection, obj_id)
                    if boot_doc:
                        if self._valid_boot_delete_token(token, boot_doc):
                            response = self._delete(obj_id)
                            if response.status_code == 200:
                                response.reason = (
                                    "Resource '%s' deleted" % doc_id)
                        else:
                            response = hresponse.HandlerResponse(403)
                    else:
                        response = hresponse.HandlerResponse(404)
                        response.reason = "Resource '%s' not found" % doc_id
                except bson.errors.InvalidId, ex:
                    self.log.exception(ex)
                    self.log.error(
                        "Wrong ID '%s' value passed as object ID", doc_id)
                    response = hresponse.HandlerResponse(400)
                    response.reason = "Wrong ID value passed as object ID"
            else:
                spec = handlers.common.query.get_query_spec(
                    self.get_query_arguments, self._valid_keys("DELETE"))
                if spec:
                    response = self._delete(spec)
                    if response.status_code == 200:
                        response.reason = (
                            "Resources identified with '%s' deleted" % spec)
                else:
                    response = hresponse.HandlerResponse(400)
                    response.reason = (
                        "No valid data provided to execute a DELETE")
        else:
            response = hresponse.HandlerResponse(403)

        return response

    def _valid_boot_delete_token(self, token, boot_doc):
        """Make sure the token is an actual delete token.

        This is an extra step in making sure the token is valid. A lab
        token, token used to send boot reports, can be used to delete boot
        reports only belonging to its lab.

        :param token: The req token.
        :type token: models.token.Token
        :param boot_doc: The document to delete.
        :type boot_doc: dict
        :return True or False.
        """
        valid_token = False

        # Just need to check if it is a lab token. A validation has already
        # occurred makig sure is a valid DELETE one.
        # This is the extra step.
        if token.is_lab_token:
            # This is only valid if the lab matches.
            lab_doc = utils.db.find_one2(
                self.db[models.LAB_COLLECTION],
                {models.NAME_KEY: boot_doc[models.LAB_NAME_KEY]})

            if lab_doc:
                lab_doc = mlab.LabDocument.from_json(lab_doc)

                if lab_doc.token == token.id:
                    valid_token = True

        return valid_token

    def _delete(self, spec_or_id, **kwargs):
        response = hresponse.HandlerResponse(200)
        response.status_code = utils.db.delete(self.collection, spec_or_id)
        response.reason = self._get_status_message(response.status_code)

        return response
