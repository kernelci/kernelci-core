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

"""The RequestHandler for /upload URLs."""

import os
import tornado.web

import handlers.base as hbase
import handlers.common as hcommon
import handlers.response as hresponse
import models
import utils.upload


class UploadHandler(hbase.BaseHandler):
    """Handler the /upload URLs."""

    def __init__(self, application, request, **kwargs):
        super(UploadHandler, self).__init__(application, request, **kwargs)

    @property
    def collection(self):
        return self.db[models.UPLOAD_COLLECTION]

    @property
    def content_type(self):
        return "multipart/form-data"

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

    def execute_delete(self, *args, **kwargs):
        """Perform DELETE pre-operations.

        Check that the DELETE request is OK.
        """
        # TODO: in the future we need to enable delete as well.
        response = None

        if self.validate_req_token("DELETE"):
            response = hresponse.HandlerResponse(501)
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def execute_post(self, *args, **kwargs):
        """Execute the POST pre-operations.

        Checks that everything is OK to perform a POST.
        """
        response = None
        if self.validate_req_token("POST"):
            valid_request = self._valid_post_request()

            if valid_request == 200:
                path = None
                # path here is considered to be a directory.
                if kwargs.get("path", None):
                    path = kwargs.get("path")
                else:
                    try:
                        job = self.get_argument(models.JOB_KEY)
                        kernel = self.get_argument(models.KERNEL_KEY)
                        defconfig = self.get_argument(models.DEFCONFIG_KEY)
                        defconfig_full = self.get_argument(
                            models.DEFCONFIG_FULL, default=None)
                        arch = self.get_argument(models.ARCHITECTURE_KEY)
                        lab = self.get_argument(
                            models.LAB_NAME_KEY, default=None)

                        defconfig_path = "-".join(
                            [arch, (defconfig_full or defconfig)])

                        path = os.path.join(job, kernel, defconfig_path)
                        if lab is not None:
                            path = os.path.join(path, lab)
                    except tornado.web.MissingArgumentError, ex:
                        self.log.exception(ex)
                        response = hresponse.HandlerResponse(ex.status_code)
                        response.reason = ex.log_message

                if path and utils.upload.is_valid_dir_path(path):
                    ret_val, reason = \
                        utils.upload.check_or_create_upload_dir(path)
                    if ret_val == 200:
                        response = self._save_files(path)
                    else:
                        response = hresponse.HandlerResponse(ret_val)
                        response.reason = reason
                else:
                    response = hresponse.HandlerResponse(400)
                    response.reason = "Provided path is not a directory"
            else:
                response = hresponse.HandlerResponse(valid_request)
                response.reason = (
                    "%s: %s" %
                    (
                        self._get_status_message(valid_request),
                        "Use %s the content type" % self.content_type
                    )
                )
        else:
            response = hresponse.HandlerResponse(403)
            response.reason = hcommon.NOT_VALID_TOKEN

        return response

    def _save_files(self, path):
        response = hresponse.HandlerResponse()

        if self.request.files:
            response.result = [
                utils.upload.create_or_update_file(
                    path,
                    u_file[0]["filename"],
                    u_file[0]["content_type"],
                    u_file[0]["body"]
                )
                for u_file in self.request.files.itervalues()
            ]
        else:
            response.status_code = 400
            response.reason = "No files provided"

        return response
