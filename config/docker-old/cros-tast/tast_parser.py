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

from functools import partial
import subprocess
import sys
import os
import json
import pwd

RESULTS_DIR = "/tmp/results"
RESULTS_CHART_FILE = "results-chart.json"
RESULTS_FILE = "results.json"
TAST_PATH = "./tast"


def fetch_dut():
    output = subprocess.check_output("lava-target-ip", shell=True).strip()
    return output


def report_lava_test_case(test_name, result, measurement=None):
    opts = ['lava-test-case', test_name, '--result', result]
    if measurement:
        opts.extend(['--measurement', str(measurement['value']),
                     '--units', str(measurement['units'])])
    subprocess.run(opts, check=False)


def report_lava_test_set(action, name):
    opts = ['lava-test-set', action, name]
    subprocess.run(opts, check=False)


lava_test_set_start = partial(report_lava_test_set, 'start')
lava_test_set_stop = partial(report_lava_test_set, 'stop')


def report_lava(test_data):
    if 'measurements' in test_data:
        lava_test_set_start(test_data['name'])
        for measurement in test_data['measurements']:
            report_lava_test_case(measurement['name'],
                                  test_data['result'],
                                  measurement)
        lava_test_set_stop(test_data['name'])
    else:
        report_lava_test_case(test_data['name'],
                              test_data['result'])


def run_tests(args):
    uid = pwd.getpwnam("cros-tast").pw_uid
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR, exist_ok=True)
    os.chown(RESULTS_DIR, uid, 0)
    remote_ip = fetch_dut()
    tast_cmd = [
        'sudo',
        '-u',
        'cros-tast',
        '--login',
        TAST_PATH,
        'run',
        f'-resultsdir={RESULTS_DIR}',
        '-sysinfo=false',
        '-build=false',
        remote_ip
    ]
    tast_cmd.extend(args)
    subprocess.run(tast_cmd, check=True)


def _get_result(test_case):
    if len(test_case["skipReason"]) > 0:
        return "skip"
    if test_case["errors"] is not None:
        return "fail"
    return "pass"


def parse_results(json_data):
    for element in json_data:
        test_data = {
            "name": element["name"],
            "result": _get_result(element),
            "outDir": element["outDir"]
        }
        yield test_data


def parse_measurements(results_chart):
    measurements = []
    for name, cases in results_chart.items():
        for sub_name, data in cases.items():
            if data["type"] == "list_of_scalar_values":
                print(f"Unsupported data type \
                    'list_of_scalar_values', skipping \
                        {'.'.join([name, sub_name])}")
                continue
            measurement = {
                "name": ".".join([name, sub_name]),
                "units": data["units"],
                "value": data["value"]
            }
            measurements.append(measurement)
    return measurements


def main(tests):
    run_tests(tests)
    json_file = os.path.join(RESULTS_DIR, RESULTS_FILE)
    with open(json_file, "r") as results_file:
        results = json.load(results_file)
    for test_data in parse_results(results):
        results_chart = os.path.join(test_data["outDir"], RESULTS_CHART_FILE)
        if os.path.isfile(results_chart):
            with open(results_chart, "r") as rc_file:
                rc_data = json.load(rc_file)
            measurements = parse_measurements(rc_data)
            test_data["measurements"] = measurements
        report_lava(test_data)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print("No tests provided")
        sys.exit(1)
