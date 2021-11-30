#!/usr/bin/env python3
#
# Copyright (C) 2022 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>
#
# This script is free software; you can redistribute it and/or modify it under
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

import subprocess
import sys
import os
import json

RESULTS_DIR = "/tmp/results"
TAST_PATH = "./tast"


def fetch_dut():
    output = subprocess.check_output("lava-target-ip", shell=True).strip()
    return output


def report_lava(testname, result):
    opts = ['lava-test-case', testname, '--result', result]
    subprocess.run(opts)


def run_tests(args):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR, exist_ok=True)
    remote_ip = fetch_dut()
    tast_cmd = [
        TAST_PATH,
        'run',
        f'-resultsdir={RESULTS_DIR}',
        '-sysinfo=false',
        '-build=false',
        remote_ip
    ]
    tast_cmd.extend(args)
    subprocess.run(tast_cmd, check=True)


def parse_results():
    json_file = os.path.join(RESULTS_DIR, 'results.json')
    with open(json_file, 'r') as fh:
        jdata = json.load(fh)
        for element in jdata:
            if len(element["skipReason"]) > 0:
                report_lava(element["name"], "skip")
                continue
            if element["errors"] is not None:
                report_lava(element["name"], "fail")
                continue
            report_lava(element["name"], "pass")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("No tests provided")
        sys.exit(1)
    run_tests(sys.argv[1:])
    parse_results()
