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
import yaml

# copied from lava-server/lava_scheduler_app/models.py
SUBMITTED = 0
RUNNING = 1
COMPLETE = 2
INCOMPLETE = 3
CANCELED = 4
CANCELING = 5

# git bisect return codes
BISECT_PASS = 0
BISECT_SKIP = 1
BISECT_FAIL = 2

# LAVA job result names
LAVA_JOB_RESULT_NAMES = {
    COMPLETE: "PASS",
    INCOMPLETE: "FAIL",
    CANCELED: "UNKNOWN",
    CANCELING: "UNKNOWN",
}

# git bisect and LAVA job status map
BOOT_STATUS_MAP = {
    COMPLETE: BISECT_PASS,
    INCOMPLETE: BISECT_FAIL,
}


def is_infra_error(cb):
    lava_yaml = cb['results']['lava']
    lava = yaml.load(lava_yaml)
    stages = {s['name']: s for s in lava}
    job_meta = stages['job']['metadata']
    return job_meta.get('error_type') == "Infrastructure"


def handle_boot(cb):
    job_status = cb['status']
    print("Status: {}".format(LAVA_JOB_RESULT_NAMES[job_status]))
    return BOOT_STATUS_MAP.get(job_status, BISECT_SKIP)


def main(args):
    with open(args.json) as json_file:
        cb = json.load(json_file)

    if args.token and cb['token'] != args.token:
        print("Token mismatch")
        sys.exit(1)

    if is_infra_error(cb):
        print("Infrastructure error")
        ret = BISECT_SKIP
    else:
        ret = handle_boot(cb)

    sys.exit(ret)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parse LAVA v2 callback data")
    parser.add_argument("json",
                        help="Path to the JSON data file")
    parser.add_argument("--token",
                        help="Secret authorization token")
    args = parser.parse_args()
    main(args)
