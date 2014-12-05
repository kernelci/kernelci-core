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

import utils.log

BASE_PATH = '/var/www/images/kernel-ci'
DEFAULT_MONGODB_URL = "localhost"
DEFAULT_MONGODB_PORT = 27017
DEFAULT_MONGODB_POOL = 250
LOG = utils.log.get_log()


def is_hidden(value):
    """Verify if a file name or dir name is hidden (starts with .).

    :param value: The value to verify.
    :return True or False.
    """
    hidden = False
    if value.startswith("."):
        hidden = True
    return hidden
