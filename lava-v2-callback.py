#!/usr/bin/env python3

# Copyright (C) 2018 Collabora Limited
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

import argparse
import json
import sys

# copied from lava-server/lava_scheduler_app/models.py
SUBMITTED = 0
RUNNING = 1
COMPLETE = 2
INCOMPLETE = 3
CANCELED = 4
CANCELING = 5


def main(args):
    with open(args.json) as json_file:
        cb = json.load(json_file)

    if args.token and cb['token'] != args.token:
        print("Token mismatch")
        sys.exit(1)

    job_status = cb['status']

    lava_job_result = {
        COMPLETE: "PASS",
        INCOMPLETE: "FAIL",
        CANCELED: "UNKNOWN",
        CANCELING: "UNKNOWN",
    }

    print("Status: {}".format(lava_job_result[job_status]))

    status_map = {
        COMPLETE: 0,
        INCOMPLETE: 2,
    }

    sys.exit(status_map.get(job_status, 1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parse LAVA v2 callback data")
    parser.add_argument("json",
                        help="Path to the JSON data file")
    parser.add_argument("--token",
                        help="Secret authorization token")
    args = parser.parse_args()
    main(args)
