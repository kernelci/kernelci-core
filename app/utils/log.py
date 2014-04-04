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

"""Logging facilities."""

import logging

log = None


def get_log(debug=False):
    """Retrieve a logger.

    :param debug: If debug level should be turned on.
    :return: A logger instance.
    """
    global log

    if log is None:
        log = logging.getLogger()
        ch = logging.StreamHandler()

        formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s [%(threadName)-10s] %(message)s'
        )

        if debug:
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            log.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.INFO)
            ch.setFormatter(formatter)
            log.setLevel(logging.INFO)

        log.addHandler(ch)

    return log
