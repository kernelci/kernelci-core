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

"""Handler utilities to work with tokens."""

import datetime

import models
import models.token as mtoken
import utils
import utils.db


def valid_token_general(token, method):
    """Make sure the token can be used for an HTTP method.

    For DELETE requests, if the token is a lab token, the request will be
    refused. The lab token can be used only to delete boot reports.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([(method == "POST" or method == "PUT"), token.is_post_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_delete_token]):
        if not token.is_lab_token:
            valid_token = True

    return valid_token


def valid_token_bh(token, method):
    """Make sure the token is a valid token for the `BootHandler`.

    This is a special case to handle a lab token (token associeated with a lab)

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([(method == "POST" or method == "PUT"), token.is_post_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_delete_token]):
        valid_token = True

    return valid_token


def valid_token_th(token, method):
    """Make sure a token is a valid token for the `TokenHandler`.

    A valid `TokenHandler` token is an admin token, or a superuser token
    for GET operations.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if token.is_admin:
        valid_token = True
    elif all([token.is_superuser, method == "GET"]):
        valid_token = True

    return valid_token


def valid_token_upload(token, method):
    """Make sure a token is enabled to upload files.

    :param token: The token object to validate.
    :param method: The HTTP method this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if any([token.is_admin, token.is_superuser]):
        valid_token = True
    if all([(method == "PUT" or method == "POST"), token.is_upload_token]):
        valid_token = True

    return valid_token


def valid_token_tests(token, method):
    """Make sure a token is enabled for test reports.

    :param token: The token object to validate.
    :param method: The HTTP method this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if any([token.is_admin, token.is_superuser]):
        valid_token = True
    elif all([method == "GET", token.is_get_token]):
        valid_token = True
    elif all([method == "PUT" or method == "POST", token.is_test_lab_token]):
        valid_token = True
    elif all([method == "DELETE", token.is_test_lab_token]):
        valid_token = True

    return valid_token


def valid_token_ip(token, remote_ip):
    """Make sure the token comes from the designated IP addresses.

    :param token: The Token object to validate.
    :param remote_ip: The remote IP address sending the token.
    :return True or False.
    """
    valid_token = False

    if token.ip_address is not None:
        if remote_ip:
            remote_ip = mtoken.convert_ip_address(remote_ip)

            if remote_ip in token.ip_address:
                valid_token = True
            else:
                utils.LOG.warn(
                    "IP restricted token from wrong IP address: %s",
                    remote_ip)
        else:
            utils.LOG.error(
                "No remote IP address provided, cannot validate token")
    else:
        valid_token = True

    return valid_token


def is_expired_token(token):
    """Verify whther a token is expired or not.

    :param token: The token to verify.
    :type token: `models.Token`.
    :return True or False.
    """
    is_expired = False

    if token.expired:
        is_expired = True
    else:
        expires_on = token.expires_on
        if all([expires_on is not None,
                isinstance(expires_on, datetime.datetime)]):
            if expires_on < datetime.datetime.now():
                is_expired = True

    return is_expired


def validate_token(token_obj, method, remote_ip, validate_func):
    """Make sure the passed token is valid.

    :param token_obj: The JSON object from the db that contains the token.
    :param method: The HTTP verb this token is being validated for.
    :param remote_ip: The remote IP address sending the token.
    :param validate_func: Function called to validate the token, must accept
        a Token object and the method string.
    :return A 2-tuple: True or False; the token object.
    """
    valid_token = True
    token = None

    if token_obj:
        token = mtoken.Token.from_json(token_obj)

        if token:
            if not isinstance(token, mtoken.Token):
                utils.LOG.error("Retrieved token is not a Token object")
                valid_token = False
            else:
                if is_expired_token(token):
                    valid_token = False
                else:
                    valid_token &= validate_func(token, method)

                    if all([valid_token,
                            token.is_ip_restricted,
                            not valid_token_ip(token, remote_ip)]):
                        valid_token = False
        else:
            valid_token = False
    else:
        valid_token = False

    return valid_token, token


def find_token(database, spec):
    """Find a token in the database.

    :param database: The database connection.
    :param spec: The document spec to look for.
    :type spec: dict
    :return A json object, or None.
    """
    # Done in this way to have life easier with testing.
    return utils.db.find_one2(database[models.TOKEN_COLLECTION], spec)


# pylint: disable=too-many-arguments
# pylint: disable=unused-argument
def token_validation(
        method,
        req_token, remote_ip, validation_func, database, master_key=None):
    """Perform the real token validation.

    :param method: The HTTP verb to validate.
    :type method: str
    :param req_token: The token as taken from the request.
    :type req_token: str
    :param remote_ip: The IP address originating the request.
    :type remote_ip: str
    :param validation_func: The special function to validate the token.
    :type validation_func: function
    :param database: The database connection.
    :param master_key: The default master key.
    :type master_key: str
    :return A 2-tuple: True or False; the token object.
    """
    valid_token = False
    token = None
    token_obj = find_token(database, {models.TOKEN_KEY: req_token})

    if token_obj:
        valid_token, token = validate_token(
            token_obj,
            method,
            remote_ip,
            validation_func
        )
    return valid_token, token
