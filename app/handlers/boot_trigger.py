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

"""The RequestHandler for /trigger/boot URLs."""

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models


class BootTriggerHandler(hbase.BaseHandler):
    """Handle the /trigger/boot URLs."""

    def __init__(self, application, request, **kwargs):
        super(BootTriggerHandler, self).__init__(
            application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.DEFCONFIG_COLLECTION]

    @staticmethod
    def _token_validation_func():
        return hcommon.valid_token_bh

    def _get(self, **kwargs):
        response = hresponse.HandlerResponse()

        # TODO: validate token and get the lab name.
        return response

    def _is_valid_token(self):
        pass
