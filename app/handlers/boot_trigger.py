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

import pymongo

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import utils.db


BOOT_TRIGGER_VALID_KEYS = {
    "GET": [
        models.ARCHITECTURE_KEY,
        models.CREATED_KEY,
        models.DEFCONFIG_FULL_KEY,
        models.DEFCONFIG_ID_KEY,
        models.DEFCONFIG_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.PRIVATE_KEY,
        models.STATUS_KEY,
    ]
}

GET_SORT_ORDER = [
    (models.CREATED_KEY, pymongo.DESCENDING),
    (models.DEFCONFIG_FULL_KEY, pymongo.ASCENDING)
]


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
        # Use the same token validation logic of the boot handler.
        return hcommon.valid_token_bh

    @staticmethod
    def _valid_keys(method):
        return BOOT_TRIGGER_VALID_KEYS.get(method, [])

    def execute_delete(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def execute_put(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def execute_post(self, *args, **kwargs):
        """Not implemented."""
        return hresponse.HandlerResponse(501)

    def execute_get(self, *args, **kwargs):
        response = None

        valid_token, token = self.validate_req_token("GET")
        is_lab, is_super, lab_name = _is_lab_token(token, self.db)

        valid_token &= is_lab

        if any([valid_token, is_super]):
            if any([lab_name, is_super]):
                kwargs["lab_name"] = lab_name
                response = self._get(**kwargs)
            else:
                response = hresponse.HandlerResponse(400)
                response.reason = "Provided token is not associated with a lab"
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _get(self, **kwargs):
        response = hresponse.HandlerResponse()
        spec, fields, skip, limit, compared = self._get_query_args()

        if compared:
            lab_name = kwargs.get("lab_name", None)
            # TODO: implement logic to retrieve data compared to other labs.
            if lab_name:
                pass
            else:
                response.status_code = 400
                response.reason = "Missing lab name to perform a comparison"
        else:
            result, count = utils.db.find_and_count(
                self.collection,
                limit,
                skip,
                spec=spec,
                fields=fields,
                sort=GET_SORT_ORDER
            )

            if count > 0:
                response.result = result
            else:
                response.result = []

            response.count = count

        response.limit = limit
        return response

    def _get_query_args(self, method="GET"):
        compared = False
        fields = None
        limit = 0
        skip = 0
        spec = {}

        if self.request.arguments:
            spec, fields, skip, limit, compared = \
                hcommon.get_trigger_query_values(
                    self.get_query_arguments, self._valid_keys(method))

        return spec, fields, skip, limit, compared


def _is_lab_token(token, database):
    """Validate the token and retrieve the lab name.

    :param token: The token to analyze.
    :type token: models.token.Token
    :param database: The connection to the database.
    :return A 3-tuple: True or False to indicate if it is a lab token;
    True or False to indicate if the token is an admin/super one; the lab
    name or None.
    """
    lab_name = None
    is_lab = is_super = False

    if token:
        if any([token.is_admin, token.is_superuser]):
            is_lab = is_super = True
        elif token.is_lab_token:
            is_lab = True
            lab_name = _get_lab_name(token, database)

    return is_lab, is_super, lab_name


def _get_lab_name(token, database):
    """Retrieve the lab name based on the provided token.

    :param token: The token object.
    :type token: models.token.Token
    :param database: The connection to the database.
    :return The lab name or None.
    """
    lab_name = None

    lab_obj = utils.db.find_one2(
        database[models.LAB_COLLECTION],
        {models.TOKEN_KEY: token.token}, [models.LAB_NAME_KEY])

    if lab_obj:
        lab_name = lab_obj[models.LAB_NAME_KEY]

    return lab_name
