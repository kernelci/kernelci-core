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

import copy
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
        models.DEFCONFIG_KEY,
        models.GIT_BRANCH_KEY,
        models.GIT_COMMIT_KEY,
        models.GIT_DESCRIBE_KEY,
        models.ID_KEY,
        models.JOB_ID_KEY,
        models.JOB_KEY,
        models.KERNEL_KEY,
        models.PRIVATE_KEY,
        models.STATUS_KEY
    ]
}


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
        spec, sort, fields, skip, limit, compared = self._get_query_args()

        if compared:
            lab_name = kwargs.get("lab_name", None)
            if lab_name:
                # The final results and count.
                result = []
                count = 0

                # First get all the defconfigs with the spec as specified
                # in the query parameters.
                all_defconfigs, all_count = utils.db.find_and_count(
                    self.collection,
                    0,
                    0,
                    spec=spec,
                    fields=[models.ID_KEY],
                    sort=sort
                )

                # If we have defconfigs, search for all the boot reports with
                # almost the same specified query, excluding the boots
                # performed by the querying lab, and looking only for the
                # defconfings similar to the ones retrieved above.
                if all_count > 0:
                    all_distinct_def = all_defconfigs.distinct(models.ID_KEY)

                    # Make a copy of the spec used to retrieve the defconfing
                    # since we need it later as well.
                    boot_spec = copy.deepcopy(spec)
                    # Remove possible query arguments that are not in the boot
                    # schema.
                    boot_spec.pop(models.GIT_BRANCH_KEY, None)
                    boot_spec.pop(models.GIT_COMMIT_KEY, None)
                    boot_spec.pop(models.GIT_DESCRIBE_KEY, None)
                    boot_spec.pop(models.ID_KEY, None)
                    # Inject the lab name and the previous defconfigs.
                    boot_spec[models.LAB_NAME_KEY] = {"$ne": lab_name}
                    boot_spec[models.DEFCONFIG_ID_KEY] = {
                        "$in": all_distinct_def}

                    already_booted, booted_count = utils.db.find_and_count(
                        self.db[models.BOOT_COLLECTION],
                        0,
                        0,
                        spec=boot_spec,
                        fields=[models.DEFCONFIG_ID_KEY],
                        sort=[(models.CREATED_KEY, pymongo.DESCENDING)]
                    )

                    booted_defconfigs = []
                    if booted_count > 0:
                        booted_defconfigs = already_booted.distinct(
                            models.DEFCONFIG_ID_KEY)

                    # Do a set difference to get the not booted ones.
                    not_booted = set(all_distinct_def).difference(
                        set(booted_defconfigs))

                    if not_booted:
                        spec[models.ID_KEY] = {"$in": list(not_booted)}

                        # These are the final results, what gets back to the
                        # user.
                        result, count = utils.db.find_and_count(
                            self.collection,
                            limit,
                            skip,
                            spec=spec,
                            fields=fields,
                            sort=sort
                        )

                response.result = result
                response.count = count
            else:
                response.status_code = 400
                response.reason = (
                    "Missing lab name to perform a comparison: "
                    "was a lab token used?")
        else:
            result, count = utils.db.find_and_count(
                self.collection,
                limit,
                skip,
                spec=spec,
                fields=fields,
                sort=sort
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
        sort = None

        if self.request.arguments:
            spec, sort, fields, skip, limit, compared = \
                hcommon.get_trigger_query_values(
                    self.get_query_arguments, self._valid_keys(method))

        return spec, sort, fields, skip, limit, compared


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
        {models.TOKEN_KEY: token._id}, [models.NAME_KEY])

    if lab_obj:
        lab_name = lab_obj[models.NAME_KEY]

    return lab_name
