# Copyright (C) 2018, 2019 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
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

import re
import subprocess
import sys

__version__ = '1.1'


def shell_cmd(cmd, ret_code=False):
    if ret_code:
        return False if subprocess.call(cmd, shell=True) else True
    else:
        return subprocess.check_output(cmd, shell=True).decode()


def print_flush(msg):
    print(msg)
    sys.stdout.flush()


def sort_check(keys):
    parsed_keys = list((tuple(re.split(r'-|_|\.', key)), key) for key in keys)
    keys_map = dict(parsed_keys)
    split_keys = list(k[0] for k in parsed_keys)
    numeric_keys = []
    for split_key in split_keys:
        numeric_keys.extend(k for k in split_key if k.isdigit())
    max_digits = max(len(k) for k in numeric_keys) if numeric_keys else 0
    fmt = '{{:0{}d}}'.format(max_digits)
    sorted_keys = sorted(
        split_keys,
        key=lambda x: list(fmt.format(int(k)) if k.isdigit() else k for k in x)
    )
    for key_raw, key_sorted in zip(split_keys, sorted_keys):
        if key_raw != key_sorted:
            return keys_map[key_raw], keys_map[key_sorted]
    return None
