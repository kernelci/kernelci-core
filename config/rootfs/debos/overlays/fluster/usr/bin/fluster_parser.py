#!/usr/bin/env python3
#
# Copyright (C) 2022 Collabora Limited
# Author: Laura Nao <laura.nao@collabora.com>
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
import os
import subprocess
import sys
import xml

from junitparser import JUnitXml, Skipped

FLUSTER_PATH = '/opt/fluster'
RESULTS_FILE = 'results.xml'


def _check(path, match):
    paths = os.environ['PATH'].split(':')
    if os.getuid() != 0:
        paths.extend(['/usr/local/sbin', '/usr/sbin', '/sbin'])
    for dirname in paths:
        candidate = os.path.join(dirname, path)
        if match(candidate):
            return candidate
    return None


def _parse_vector_result(vector):
    if vector.result:
        if isinstance(vector.result[0], Skipped):
            res = 'skip'
        else:
            res = 'fail'
    else:
        res = 'pass'
    return vector.name, res


def _load_results_file(filename):
    ret = None
    try:
        f = open(filename, 'r')
        try:
            ret = JUnitXml.fromfile(f)
        except xml.etree.ElementTree.ParseError as e:
            print(f'Error parsing {filename} file: {e}')
        finally:
            f.close()
    except IOError as e:
        print(e)

    return ret


def _run_fluster(test_suite=None):
    cmd = ['python3', 'fluster.py', '-ne', 'run',
           '-j1', '-f', 'junitxml', '-so', RESULTS_FILE]

    if test_suite:
        cmd.extend(['-ts', test_suite])

    subprocess.run(cmd, cwd=FLUSTER_PATH, check=False)


def main(args):
    cmd = {
        'set': 'lava-test-set',
        'case': 'lava-test-case'
    }

    if not _check(path=cmd['case'], match=os.path.isfile):
        cmd = cmd.fromkeys(cmd, 'echo')

    # run fluster tests
    _run_fluster(args.test_suite)

    # load test results
    junitxml = _load_results_file(f'{FLUSTER_PATH}/{RESULTS_FILE}')

    if not junitxml:
        subprocess.check_call([
            cmd['case'], 'validate-fluster-results', '--result', 'fail'])
        return 1

    subprocess.check_call([
        cmd['case'], 'validate-fluster-results', '--result', 'pass'])

    # parse test results
    for test_suite in junitxml:
        decoder = next(test_suite.properties()).value
        subprocess.check_call([
            cmd['set'], 'start', f'{test_suite.name}-{decoder}'])

        for res in map(_parse_vector_result, test_suite):
            case_name, case_res = res
            subprocess.check_call([
                cmd['case'], f'{case_name}', '--result', f'{case_res}'])

        subprocess.check_call([
            cmd['set'], 'stop'])
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ts', '--test-suite')
    args = parser.parse_args()
    sys.exit(main(args))
