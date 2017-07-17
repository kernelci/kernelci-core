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

"""The RequestHandler for /callback URLs."""

import tornado.web

import handlers.base as hbase
import handlers.common.query
import handlers.common.token
import handlers.response as hresponse
import models
import models.token as mtoken
import taskqueue.tasks.callback as taskq
import utils.callback.lava
import utils.db


class CallbackHandler(hbase.BaseHandler):
    """Base handler for the /callback URLs."""

    def __init__(self, application, request, **kwargs):
        super(CallbackHandler, self).__init__(application, request, **kwargs)

    @staticmethod
    def _valid_keys(method):
        """Return the valid keys for the JSON response.

        Subclasses should provide their own method. It should return either a
        list or a dictionary.
        """
        return None

    @staticmethod
    def _token_validation_func():
        # Reuse the same token logic validation for the boot resource.
        return handlers.common.token.valid_token_bh

    def execute_get(self, *args, **kwargs):
        return hresponse.HandlerResponse(501)

    def execute_delete(self, *args, **kwargs):
        return hresponse.HandlerResponse(501)

    def execute_put(self, *args, **kwargs):
        return hresponse.HandlerResponse(501)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse()

        try:
            lab_name = self.get_query_argument(models.LAB_NAME_KEY)
            req_token = kwargs["token"]

            valid_lab, error = self._is_valid_token(req_token, lab_name)
            if valid_lab:
                response.status_code = 202
                response.reason = "Request accepted and being imported"
                self._execute_callback(kwargs["json_obj"], lab_name)
            else:
                response.status_code = 403
                response.reason = (
                    "Provided authentication token is not associated with "
                    "lab '%s' or is not valid" % lab_name)

            response.errors = error
        except tornado.web.MissingArgumentError:
            response.status_code = 400
            response.reason = 'Missing lab name in query string'

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
                        "Received callback POST request from an admin token")
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

    def _execute_callback(self, json_obj, lab_name):
        """A wrapper for the real callback execution logic.

        This should be an async operation.

        :param json_obj: The JSON data to parse.
        :type json_obj: dict
        """
        # TODO: need actual implementation logic.
        pass


class LavaCallbackHandler(CallbackHandler):
    """Handler specialized to parse LAVA callbacks.

    Bound to /callback/lava
    """

    @staticmethod
    def _valid_keys(method):
        return models.LAVA_CALLBACK_VALID_KEYS.get(method, None)

    def _execute_callback(self, json_obj, lab_name):
        taskq.lava_boot.apply_async([json_obj, lab_name])
