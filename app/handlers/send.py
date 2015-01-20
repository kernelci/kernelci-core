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

"""This module is used to send boot and build report email."""

import bson
import datetime

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import taskqueue.tasks as taskq


# pylint: disable=too-many-public-methods
class SendHandler(hbase.BaseHandler):
    """Handle the /send URLs."""

    def __init__(self, application, request, **kwargs):
        super(SendHandler, self).__init__(application, request, **kwargs)

    @staticmethod
    def _valid_keys(method):
        return hcommon.SEND_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(202)

        json_obj = kwargs["json_obj"]
        db_options = kwargs["db_options"]
        mail_options = self.settings["mailoptions"]

        countdown = json_obj.get(models.DELAY_KEY, self.settings["senddelay"])
        if countdown is None:
            countdown = self.settings["senddelay"]

        try:
            countdown = abs(int(countdown))
            when = (
                datetime.datetime.now(tz=bson.tz_util.utc) +
                datetime.timedelta(seconds=countdown)
            )
            response.reason = (
                "Email report scheduled to be sent at '%s' UTC" %
                when.isoformat()
            )

            taskq.schedule_boot_report.apply_async(
                [json_obj, db_options, mail_options, countdown])
        except (TypeError, ValueError):
            response.status_code = 400
            response.reason = (
                "Wrong value specified for 'delay': %s" % countdown
            )

        return response

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        response = None

        if self.validate_req_token("DELETE"):
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def execute_get(self, *args, **kwargs):
        """Execute the GET pre-operations.

        Checks that everything is OK to perform a GET.
        """
        response = None

        if self.validate_req_token("GET"):
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response
