#!/usr/bin/python
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


def get_device_type_by_name(name, device_types, aliases=[]):
    """
        Return a device type named name. In the case of an alias, resolve the
        alias to a device_type

        Example:
        IN:
            name = "x15"
            device_types = [
              {'busy': 1, 'idle': 0, 'name': 'x15', 'offline': 0},
              {'busy': 1, 'idle': 0, 'name': 'beaglebone-black', 'offline': 0},
            ]
            aliases = [
              {'name': 'am57xx-beagle-x15', 'device_type': 'x15'}
            ]
        OUT:
            {'busy': 1, 'idle': 0, 'name': 'x15', 'offline': 0}

    """
    for device_type in device_types:
        if device_type["name"] == name:
            return device_type
    for alias in aliases:
        if alias["name"] == name:
            for device_type in device_types:
                if alias["device_type"] == device_type["name"]:
                    return device_type
    return None
