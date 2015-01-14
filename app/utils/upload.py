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

"""Utility functions to handle file uploads."""

import io
import os

import utils


def is_valid_dir_path(path):
    """Verify if the provided path is valid as a directory.

    A valid path must be a directory or it does not have to exists.

    :param path: The path to verify.
    :type path: str
    :return True or False.
    """
    is_valid = True
    real_path = os.path.join(utils.BASE_PATH, path)
    if os.path.exists(real_path):
        if not os.path.isdir(real_path):
            is_valid = False
    return is_valid


def create_upload_dir(path):
    ret_val = 200
    error = None
    real_path = os.path.join(utils.BASE_PATH, path)

    if not os.path.exists(real_path):
        try:
            os.makedirs(real_path)
        except OSError, ex:
            utils.LOG.exception(ex)
            ret_val = 500
            error = "Unable to access destination directory '%s'" % path

    return ret_val, error


def create_or_update_path(path, filename, content_type, content):
    ret_dict = {
        "status": 200,
        "error": None,
        "bytes": 0,
        "filename": filename
    }

    file_path = os.path.join(path, filename)
    real_path = os.path.join(utils.BASE_PATH, file_path)

    utils.LOG.info("Writing file '%s'", real_path)

    try:
        with io.open(real_path, mode="bw") as w_file:
            ret_dict["bytes"] = w_file.write(content)
    except IOError, ex:
        utils.LOG.exception(ex)
        utils.LOG.error("Unable to open file '%s'", file_path)
        ret_dict["status"] = 500
        ret_dict["error"] = "Error writing file '%s'" % filename

    return ret_dict
