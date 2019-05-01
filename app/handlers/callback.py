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
from celery import chain
import yaml

import handlers.base as hbase
import handlers.common.query
import handlers.common.token
import handlers.response as hresponse
import models
import models.token as mtoken
import taskqueue.tasks.boot
import taskqueue.tasks.callback
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
        try:
            lab_name = self.get_query_argument(models.LAB_NAME_KEY)
            req_token = kwargs["token"]
            valid_lab, error = self._is_valid_token(req_token, lab_name)
            if not valid_lab:
                response = hresponse.HandlerResponse(403)
                response.reason = (
                    "Provided authentication token is not associated with "
                    "lab '%s' or is not valid" % lab_name)
            else:
                response = self._execute_callback(lab_name, **kwargs)
        except tornado.web.MissingArgumentError:
            response = hresponse.HandlerResponse(400)
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

    def _execute_callback(self, lab_name, **kwargs):
        """A wrapper for the real callback execution logic.

        This should be an async operation.

        :param lab_name: Name of the lab
        :type lab_name: string
        """
        return hresponse.HandlerResponse(404)


class LavaCallbackHandler(CallbackHandler):
    """Handler specialized to parse LAVA callbacks.

    Bound to /callback/lava/<action>
    """

    def __init__(self, *args, **kwargs):
        super(LavaCallbackHandler, self).__init__(*args, **kwargs)
        self._json_obj = None
        self._job_meta = None

    @property
    def json_obj(self):
        return self._json_obj

    @property
    def job_meta(self):
        return self._job_meta

    @staticmethod
    def _valid_keys(method):
        return models.LAVA_CALLBACK_VALID_KEYS.get(method, None)

    def is_valid_json(self, json_obj, **kwargs):
        valid, errors = super(LavaCallbackHandler, self).is_valid_json(
            json_obj, **kwargs)
        if not valid:
            return valid, errors
        definition = yaml.load(json_obj["definition"], Loader=yaml.CLoader)
        job_meta = definition.get("metadata")
        if not job_meta:
            return False, "metadata missing from LAVA job definition"
        self._json_obj = json_obj
        self._job_meta = job_meta
        action = kwargs["action"]
        keys = models.LAVA_CALLBACK_VALID_METADATA_KEYS.get(action, [])
        mandatory_keys = keys[models.MANDATORY_KEYS]
        accepted_keys = keys[models.ACCEPTED_KEYS]
        all_keys = mandatory_keys + accepted_keys
        job_meta_keys = job_meta.keys()
        for k in job_meta_keys:
            if k not in all_keys:
                return False, "invalid LAVA metadata: {}".format(k)
        for k in mandatory_keys:
            if k not in job_meta_keys:
                return False, "missing mandatory LAVA metadata: {}".format(k)
        return True, ''

    def _execute_callback(self, lab_name, **kwargs):
        action = kwargs["action"]
        response = hresponse.HandlerResponse()
        response.status_code = 202
        response.reason = "Request accepted and being processed"

        if action in ["boot", "test"]:
            tasks = [
                taskqueue.tasks.callback.lava_test.s(
                    self.json_obj, self.job_meta, lab_name),
            ]
            if action == "test":
                tasks.append(taskqueue.tasks.test.find_regression.s())
            chain(tasks).apply_async(
                link_error=taskqueue.tasks.error_handler.s())
        else:
            response.status_code = 404
            response.reason = "Unsupported LAVA action: {}".format(action)

        # Also run the legacy boot callback to generate boot entries
        if action == "boot":
            tasks = [
                taskqueue.tasks.callback.lava_boot.s(
                    self.json_obj, self.job_meta, lab_name),
                taskqueue.tasks.boot.find_regression.s(),
            ]
            chain(tasks).apply_async(
                link_error=taskqueue.tasks.error_handler.s())

        return response
