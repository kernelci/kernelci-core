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

"""The /batch RequestHandler to perform batch operations."""

from json import loads as j_load

from handlers.base import BaseHandler
from handlers.common import BATCH_VALID_KEYS
from handlers.response import HandlerResponse
from models import BATCH_KEY
from taskqueue.tasks import run_batch_group
from utils.validator import is_valid_batch_json


class BatchHandler(BaseHandler):

    def __init__(self, application, request, **kwargs):
        super(BatchHandler, self).__init__(application, request, **kwargs)
        self._operations = []

    @staticmethod
    def _valid_keys(method):
        return BATCH_VALID_KEYS.get(method, None)

    def execute_get(self):
        return HandlerResponse(501)

    def execute_delete(self):
        return HandlerResponse(501)

    def execute_post(self):
        response = None
        valid_request = self._valid_post_request()

        if valid_request == 200:
            try:
                json_obj = j_load(self.request.body.decode('utf8'))

                if is_valid_batch_json(
                        json_obj, BATCH_KEY, self._valid_keys('POST')):
                    response = HandlerResponse(200)
                    response.result = \
                        self.prepare_and_perform_batch_operations(
                            json_obj
                        )
                else:
                    response = HandlerResponse(422)
                    response.reason = "Provided JSON is not valid"
                    response.result = None
            except ValueError:
                error = "No JSON data found in the POST request"
                self.log.error(error)
                response = HandlerResponse(422)
                response.reason = error
                response.result = None
        else:
            response = HandlerResponse(valid_request)
            response.reason = self._get_status_message(valid_request)
            response.result = None

        return response

    @staticmethod
    def prepare_and_perform_batch_operations(json_obj):
        """Perform the operation defined in the JSON object.

        The JSON oject must be a valid batch operations object.

        :param json_obj: The JSON object that defines all the bath operations
        to perform.
        :type json_obj: dict
        """
        return run_batch_group(json_obj.get(BATCH_KEY))
