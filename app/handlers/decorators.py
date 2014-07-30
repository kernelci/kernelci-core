# Copyright (C) 2014 Linaro Ltd.
#
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

"""Decorators used by handler methods."""

from functools import wraps

from models.token import (
    TOKEN_COLLECTION,
    Token,
)
from utils.db import find_one

API_TOKEN_HEADER = 'X-Linaro-Token'


def protected(method):
    """Protects an HTTP method with token based auth/authz.

    :param method: The HTTP verb to protect.
    """

    def decorator_wrap(function):
        @wraps(function)
        def _function_wrapper(obj, *args, **kwargs):
            token = obj.request.headers.get(API_TOKEN_HEADER, None)

            if token:
                token_obj = _find_token(token, obj)

                if token_obj and _validate_token(
                        token_obj, obj, method, _valid_token_general):
                    return function(obj, *args, **kwargs)

            obj.log.info(
                "Token not authorized for IP address %s - Token: %s",
                obj.request.remote_ip, token
            )
            obj.send_error(403)

        return _function_wrapper

    return decorator_wrap


def protected_th(method):
    """Protect HTTP method with token auth/authz for the token RequestHandler.

    :param method: The HTTP verb to protect.
    """

    def decorator_wrap(function):
        @wraps(function)
        def _function_wrapper(obj, *args, **kwargs):
            token = obj.request.headers.get(API_TOKEN_HEADER, None)

            if token:
                if _is_master_key(token, obj):
                    obj.log.info(
                        "Master key in use from IP address %s",
                        obj.request.remote_ip
                    )
                    return function(obj, *args, **kwargs)
                else:
                    token_obj = _find_token(token, obj)

                    if token_obj and _validate_token(
                            token, obj, method, _valid_token_th):
                        return function(obj, *args, **kwargs)

            obj.log.info(
                "Token not authorized nor a master key for IP "
                "address %s - Token: %s", obj.request.remote_ip, token
            )
            obj.send_error(403)

        return _function_wrapper

    return decorator_wrap


def _validate_token(token, obj, method, validate_func):
    """Make sure the passed token is valid.

    :param token: The Token object to validate.
    :param obj: The RequestHandler object of this request.
    :param method: The HTTP verb this token is being validated for.
    :param validate_func: Function called to validate the token, must accept
        a Token object and the method string.
    :return True or False.
    """
    valid_token = True

    if token.is_ip_restricted and not _valid_token_ip(token, obj):
        valid_token = False

    valid_token &= validate_func(token, method)

    return valid_token


def _valid_token_th(token, method):
    """Make sure a token is a valid token for the `TokenHandler`.

    A valid `TokenHandler` token is an admin token, or a superuser token
    for GET operations.

    :param token: The Token object to validate.
    :param method: The HTTP verb to validate.
    :return True or False.
    """
    valid_token = False

    if token.is_admin:
        valid_token = True
    elif token.is_superuser and method == "GET":
        valid_token = True

    return valid_token


def _valid_token_general(token, method):
    """Make sure the token can be used for an HTTP method.

    :param token: The Token object to validate.
    :param method: The HTTP verb this token is being validated for.
    :return True or False.
    """
    valid_token = False

    if method == "GET" and token.is_get_token:
        valid_token = True
    elif method == "POST" and token.is_post_token:
        valid_token = True
    elif method == "DELETE" and token.is_delete_token:
        valid_token = True

    return valid_token


def _valid_token_ip(token, obj):
    """Make sure the token comes from the designated IP addresses.

    :param token: The Token object to validate.
    :param obj: The RequestHandler object of this request.
    :return True or False.
    """
    valid_token = True

    # TODO: what if we have a pool of IPs for the token?
    if token.ip_address != obj.request.remote_ip:
        obj.log.info(
            "IP restricted token from wrong IP address: %s",
            obj.request.remote_ip
        )
        valid_token = False

    return valid_token


def _is_master_key(token, obj):
    """Is the token a master key?

    :param token: The token to check.
    :param obj: The RequestHandler object as passed by the decorator.
    :return True or False.
    """
    is_valid = False

    obj.log.debug(
        "Checking master key from IP address %s", obj.request.remote_ip
    )

    if obj.settings['master_key'] == token:
        is_valid = True

    return is_valid


def _find_token(token, obj):
    """Find a token in the database.

    :param token: The token to find.
    :param obj: The RequestHandler object as passed by the decorator.
    :return A Token object.
    """
    token_found = None
    result = find_one(obj.db[TOKEN_COLLECTION], [token], field='token')

    if result:
        token_found = Token.from_json(result)

    return token_found
