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
    """Verify if the provided path is a valid directory.

    A valid path must be a directory or it does not have to exists.

    :param path: The path to verify.
    :type path: str
    :return True or False.
    """
    is_valid = True
    real_path = os.path.join(utils.BASE_PATH, os.path.dirname(path))
    if os.path.exists(real_path):
        if not os.path.isdir(real_path):
            is_valid = False
    return is_valid


def file_exists(path):
    """Verify if the path exists and is a file.

    :param path: The file path to check.
    :type path: str
    :return True or False.
    """
    it_exists = False
    real_path = os.path.join(utils.BASE_PATH, path)
    if os.path.isfile(real_path):
        it_exists = True
    return it_exists


def check_or_create_file_upload_dir(path):
    """Check if the path exists and it can be accessed, or create it.

    This accepts the path with the filename in it and checks if the destination
    directory exists.

    :param path: The full path to the file to check.
    :type path: str
    :return A tuple with status code and error. Status code will be 200 in case
    it is OK, 500 in case of error.
    """
    return check_or_create_upload_dir(os.path.dirname(path))


def check_or_create_upload_dir(path):
    """Check if the path exists and it can be accessed, or create it.

    :param path: The path to verify.
    :type path: str
    :return A tuple with status code and error. Status code will be 200 in case
    it is OK, 500 in case of error.
    """
    ret_val = 200
    error = None
    real_path = os.path.join(utils.BASE_PATH, path)

    if os.path.exists(real_path):
        os.access(real_path, os.R_OK | os.W_OK | os.X_OK)
    else:
        try:
            os.makedirs(real_path, mode=0775)
        except OSError, ex:
            utils.LOG.exception(ex)
            ret_val = 500
            error = "Unable to create destination directory '%s'" % path

    return ret_val, error


def create_or_update_file(path, filename, content_type, content):
    """Create or replace a file.

    :param path: The path where the file should be saved.
    :type path: str
    :param filename: The name of the file to save.
    :type filename: str
    :param content_type: The media type of the file.
    :type content_type: str
    :param content: The content of the file.
    :type content: str
    :return A dictionary that contains the status code of the operation, an
    error string if it occurred, the bytes written and the file name.
    """
    ret_dict = {
        "status": 201,
        "error": None,
        "bytes": 0,
        "filename": filename
    }

    file_path = os.path.join(path, filename)
    real_path = os.path.join(utils.BASE_PATH, file_path)

    if os.path.exists(real_path):
        ret_dict["status"] = 200

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
