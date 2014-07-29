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


def is_valid_json(json_obj, accepted_keys):
    """Validate JSON object for PUT request.

    To be invalid, just one of the keys passed needs not to be found, or there
    are no keys passed.

    :param json_obj: The JSON object to validate. It will be treated as a
                     Python dictionary.
    :param accepted_keys: A list of keys that needs to be found in the JSON
                          object.
    :return True or False.
    """
    is_valid = True
    json_keys = json_obj.keys()

    if accepted_keys:
        for key in json_keys:
            if key not in accepted_keys:
                is_valid &= False
                break
    else:
        is_valid = False

    return is_valid
