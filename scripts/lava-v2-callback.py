#!/usr/bin/env python3

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

TEST_CASE_STATUS_MAP = {
    'pass': BISECT_PASS,
    'skip': BISECT_SKIP,
    'fail': BISECT_FAIL,
}


def is_infra_error(cb):
    lava_yaml = cb['results']['lava']
    lava = yaml.load(lava_yaml)
    stages = {s['name']: s for s in lava}
    job_meta = stages['job']['metadata']
    return job_meta.get('error_type') == "Infrastructure"


def handle_boot(cb, verbose):
    job_status = cb['status']
    print("Status: {}".format(LAVA_JOB_RESULT_NAMES[job_status]))
    return BOOT_STATUS_MAP.get(job_status, BISECT_SKIP)


def _add_login_case(results, tests):
    tests_map = {t['name']: t for t in tests}
    login = tests_map.get('auto-login-action') or tests_map.get('login-action')
    job_result = tests_map['job']['result']
    result = login and login['result'] == 'pass' and job_result == 'pass'
    results['login'] = 'pass' if result else 'fail'


def _add_test_results(results, tests, suite_name):
    suite_name = suite_name.partition("_")[2]
    suite_results = results[suite_name] = dict()
    test_sets = dict()
    for test in reversed(tests):
        test_set_name = test['metadata'].get('set')
        if test_set_name:
            test_cases = suite_results.setdefault(test_set_name, dict())
        else:
            test_cases = suite_results
        test_cases[test['name']] = test['result']


def _parse_results(data):
    results = dict()
    for suite_name, suite_results in data.items():
        tests = yaml.load(suite_results, Loader=yaml.CLoader)
        if suite_name == 'lava':
            _add_login_case(results, tests)
        else:
            _add_test_results(results, tests, suite_name)
    return results


def _get_dotted_test_names(results, dotted, path=None):
    for name, value in results.items():
        res_path = list() if path is None else list(path)
        res_path.append(name)
        if isinstance(value, dict):
            _get_dotted_test_names(value, dotted, res_path)
        else:
            dotted['.'.join(res_path)] = value


def handle_test(cb, full_case_name, verbose):
    results = _parse_results(cb['results'])
    groups = list(k for (k, v) in results.items() if isinstance(v, dict))
    plan_name = yaml.safe_load(cb['definition'])['metadata']['test.plan']
    if len(groups) == 1 and groups[0] == plan_name:
        group = results[plan_name]
        cases = {k: v for (k, v) in results.items() if not isinstance(v, dict)}
        group.update(cases)
        results = {plan_name: group}
    else:
        results = {plan_name: results}
    if verbose:
        print("Results:")
        print(json.dumps(results, indent='  '))
    dotted = dict()
    _get_dotted_test_names(results, dotted)

    test_case_result = dotted.get(full_case_name)
    print("{}: {}".format(full_case_name, test_case_result))
    if test_case_result is None:
        print("Warning: failed to find result for {}".format(full_case_name))
        return BISECT_SKIP
    return TEST_CASE_STATUS_MAP[test_case_result]


def main(args):
    with open(args.json) as json_file:
        cb = json.load(json_file)

    if args.token and cb['token'] != args.token:
        print("Token mismatch")
        sys.exit(1)

    if is_infra_error(cb):
        print("Infrastructure error")
        ret = BISECT_SKIP
    elif args.test_case:
        ret = handle_test(cb, args.test_case, args.verbose)
    else:
        ret = handle_boot(cb, args.verbose)

    sys.exit(ret)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parse LAVA v2 callback data")
    parser.add_argument("json",
                        help="Path to the JSON data file")
    parser.add_argument("--token",
                        help="Secret authorization token")
    parser.add_argument("--test-case",
                        help="Test case path in dotted syntax")
    parser.add_argument("--verbose", action='store_true',
                        help="Verbose output")
    args = parser.parse_args()
    main(args)
