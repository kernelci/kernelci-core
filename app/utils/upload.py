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

import errno
import io
import os

import utils


def is_valid_dir_path(path, base_path=utils.BASE_PATH):
    """Verify if the provided path is a valid directory.

    A valid path must be a directory or it does not have to exists.

    :param path: The path to verify.
    :type path: str
    :return True or False.
    """
    is_valid = True
    real_path = os.path.join(base_path, os.path.dirname(path))
    if os.path.exists(real_path):
        if not os.path.isdir(real_path):
            is_valid = False
    return is_valid


def file_exists(path, base_path=utils.BASE_PATH):
    """Verify if the path exists and is a file.

    :param path: The file path to check.
    :type path: str
    :return True or False.
    """
    it_exists = False
    real_path = os.path.join(base_path, path)
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


def check_or_create_upload_dir(path, base_path=utils.BASE_PATH):
    """Check if the path exists and it can be accessed, or create it.

    :param path: The path to verify.
    :type path: str
    :return A tuple with status code and error. Status code will be 200 in case
    it is OK, 500 in case of error.
    """
    ret_val = 200
    error = None
    real_path = os.path.join(base_path, path)

    if os.path.exists(real_path):
        if not os.access(real_path, os.R_OK | os.W_OK | os.X_OK):
            ret_val = 500
            error = "Unable to access destination directory '%s'" % path
    else:
        try:
            os.makedirs(real_path, mode=0775)
        except OSError, ex:
            # errno.EEXIST (17) means the directory already exists, so do not
            # treat it as an error.
            if ex.errno != errno.EEXIST:
                utils.LOG.exception(ex)
                ret_val = 500
                error = "Unable to create destination directory '%s'" % path

    return ret_val, error


def create_or_update_file(path,
                          filename,
                          content_type, content, base_path=utils.BASE_PATH):
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
    real_path = os.path.join(base_path, file_path)

    # Check if the file to upload is in a subdirectory of the provided path.
    file_dir = os.path.dirname(file_path)
    if path and all([path[-1] == "/", file_dir[-1] != "/"]):
        file_dir += "/"

    ret_val = 200
    if file_dir != path:
        ret_val, err = check_or_create_upload_dir(
            file_dir, base_path=base_path)

    if ret_val == 200:
        if os.path.exists(real_path):
            # 201 means created anew, 200 means just OK, as in HTTP.
            ret_dict["status"] = 200

        utils.LOG.info("Writing file '%s'", real_path)

        w_stream = None
        try:
            w_stream = io.open(real_path, mode="bw")
            ret_dict["bytes"] = w_stream.write(content)
            w_stream.flush()
        except IOError, ex:
            utils.LOG.exception(ex)
            utils.LOG.error("Unable to open file '%s'", file_path)
            ret_dict["status"] = 500
            ret_dict["error"] = "Error writing file '%s'" % filename
        finally:
            if w_stream:
                w_stream.close()
    else:
        ret_dict["status"] = 500
        ret_dict["error"] = "Error creating upload dir '%s'" % file_dir

    return ret_dict
