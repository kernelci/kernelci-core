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

"""The RequestHandler for /defconfig URLs."""

import handlers.base as hbase
import handlers.response as hresponse
import models
import taskqueue.tasks as taskq
import utils.db


class DefConfHandler(hbase.BaseHandler):
    """Handle the /defconfig URLs."""

    def __init__(self, application, request, **kwargs):
        super(DefConfHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.DEFCONFIG_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.DEFCONFIG_VALID_KEYS.get(method, None)

    def _post(self, *args, **kwargs):
        response = hresponse.HandlerResponse(202)
        response.reason = "Request accepted and being imported"

        json_obj = kwargs["json_obj"]
        db_options = kwargs["db_options"]

        self.log.info(
            "Importing defconfig for %s-%s-%s-%s",
            json_obj[models.JOB_KEY], json_obj[models.KERNEL_KEY],
            json_obj[models.ARCHITECTURE_KEY], json_obj[models.DEFCONFIG_KEY]
        )

        taskq.import_build.apply_async(
            [json_obj, db_options],
            link=[
                taskq.parse_single_build_log.s(db_options)
            ]
        )

        return response

    def _delete(self, defconf_id, **kwargs):
        response = hresponse.HandlerResponse()
        response.status_code = utils.db.delete(self.collection, defconf_id)

        if response.status_code == 200:
            response.reason = "Resource '%s' deleted" % defconf_id

        return response
