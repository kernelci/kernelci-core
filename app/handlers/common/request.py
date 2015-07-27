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

import utils


def has_valid_content_type(headers, remote_ip):
    """Check if the Content-Type header is set correctly.

    :param headers: The headers of the request to check.
    :type headers: dict
    :param remote_ip: The remote IP address.
    :type remote_ip: str
    :return True or False.
    """
    is_valid = False

    if "Content-Type" in headers.viewkeys():
        if headers["Content-Type"].startswith("application/json"):
            is_valid = True
        else:
            utils.LOG.error(
                "Received wrong content type ('%s') from IP '%s'",
                headers["Content-Type"], remote_ip)

    return is_valid


def valid_post_request(headers, remote_ip):
    """Check that a POST request is valid.

    :param headers: The headers of the request.
    :type headers: dict
    :param remote_ip: The remote IP address.
    :type remote_ip: str
    :return 200 in case is valid, 415 if not.
    """
    return_code = 200

    if not has_valid_content_type(headers, remote_ip):
        return_code = 415

    return return_code
