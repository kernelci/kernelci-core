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

"""The RequestHandler for /boot[/<id>]/regressions/ URLs."""

import bson

import handlers.base as hbase
import handlers.response as hresponse
import models
import utils.db

from utils.boot.regressions import (
    REGRESSION_FMT,
    get_regressions_by_key,
    sanitize_key
)


class BootRegressionsHandler(hbase.BaseHandler):
    """Handle boot regressions request."""

    def __init__(self, application, request, **kwargs):
        super(BootRegressionsHandler, self).__init__(
            application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.BOOT_REGRESSIONS_COLLECTION]

    @staticmethod
    def _valid_keys(method):
        return models.BOOT_REGRESSIONS_VALID_KEYS.get(method, None)

    def _get_one(self, doc_id, **kwargs):
        """Get just one single document from the collection.

        Subclasses should override this method and implement their own
        search functionalities. This is a general one.
        It should return a `HandlerResponse` object, with the `result`
        attribute set with the operation results.

        :return A `HandlerResponse` object.
        """
        response = None

        try:
            obj_id = bson.objectid.ObjectId(doc_id)
        except bson.errors.InvalidId, ex:
            self.log.exception(ex)
            self.log.error("Provided doc ID '%s' is not valid", doc_id)
            response = hresponse.HandlerResponse()
            response.status_code = 400
            response.reason = "Wrong ID value provided"
        else:
            response = self.find_regressions(obj_id)

        return response

    def find_regressions(self, doc_id):
        """Look for the regressions a boot report.

        :param doc_id: The id of the boot report to look for regressions.
        :type doc_id: ObjectId
        :return HandlerResponse A HandlerResponse object.
        """
        response = hresponse.HandlerResponse()
        # First make sure we have a valid boot_id value.
        boot_doc = utils.db.find_one2(
            self.db[models.BOOT_COLLECTION], doc_id)

        if boot_doc:
            regr_idx_doc = utils.db.find_one2(
                self.db[models.BOOT_REGRESSIONS_BY_BOOT_COLLECTION],
                {models.BOOT_ID_KEY: doc_id})

            if regr_idx_doc:
                spec = {
                    models.ID_KEY:
                        regr_idx_doc[models.BOOT_REGRESSIONS_ID_KEY]
                }

                result = utils.db.find_one2(
                    self.collection, spec, fields=[models.REGRESSIONS_KEY])

                if result:
                    response.result = get_regressions_by_key(
                        self.generate_regression_key(boot_doc),
                        result[models.REGRESSIONS_KEY])
                    response.count = len(response.result)
        else:
            response.status_code = 404
            response.reason = "Resource '{:s}' not found".format(str(doc_id))

        return response

    @staticmethod
    def generate_regression_key(boot_doc):
        """Generate the regressions key for this boot report.

        The key is used to lookup the boot report regressions in the
        regressions data structure.

        :param boot_doc: The boot report document.
        :type boot_doc: dict
        :return str The boot regression key.
        """
        b_get = boot_doc.get

        arch = b_get(models.ARCHITECTURE_KEY)
        b_instance = \
            sanitize_key(str(b_get(models.BOARD_INSTANCE_KEY)).lower())
        board = sanitize_key(b_get(models.BOARD_KEY))
        compiler = sanitize_key(str(b_get(models.COMPILER_VERSION_EXT_KEY)))
        defconfig = sanitize_key(b_get(models.DEFCONFIG_FULL_KEY))
        lab = b_get(models.LAB_NAME_KEY)

        return REGRESSION_FMT.format(
            lab, arch, board, b_instance, defconfig, compiler)
