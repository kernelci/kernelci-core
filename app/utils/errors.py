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

"""Functions and classes to handle errors data structure."""


class BackendError(Exception):

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return ", ".join([" ".join([str(k)] + v)
                          for k, v in self.errors.iteritems()])


def update_errors(to_update, errors):
    """Update the errors dictionary from another one.

    :param to_update: The dictionary to be updated.
    :type to_update: dictionary
    :param errors: The dictionary whose elements will be added.
    :type errors: dictionary
    """
    if errors:
        to_update_keys = to_update.viewkeys()
        for k, v in errors.iteritems():
            if k in to_update_keys:
                to_update[k].extend(v)
            else:
                to_update[k] = v


def add_error(errors, err_code, err_msg):
    """Add error code and message to the provided dictionary.

    :param errors: The dictionary that will store the error codes and messages.
    :type errors: dictionary
    :param err_code: The error code that will be used as a key.
    :type err_code: int
    :param err_msg: The message to store.
    :type err_msg: string
    """
    if all([err_code, err_msg]):
        if err_code in errors.viewkeys():
            errors[err_code].append(err_msg)
        else:
            errors[err_code] = []
            errors[err_code].append(err_msg)
