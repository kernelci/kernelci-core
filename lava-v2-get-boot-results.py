#!/usr/bin/env python
#
# Copyright (C) 2017 Collabora Limited
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
import os
import requests
import sys
import time
import urlparse
import yaml
from lib import configuration


def get_boot(token, api, meta, lab):
    params_map = {
        'job': 'kernel.tree',
        'kernel': 'git.describe',
        'arch': 'job.arch',
        'device_type': 'device.type',
        'defconfig': 'kernel.defconfig_base',
    }
    params = {k: meta[v] for k, v in params_map.iteritems()}
    params['lab_name'] = lab
    api_url = urlparse.urljoin(api, '/boot/')
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }
    resp = requests.get(api_url, headers=headers, params=params)
    resp.raise_for_status()
    boots = json.loads(resp.content)['result']
    for b in boots:
        if b['defconfig_full'] == meta['kernel.defconfig']:
            return b
    return None


def poll_boot(token, api, meta, lab, args):
    start_time = time.time()
    print("Looking for boot: {} {}".format(
        meta['git.describe'], meta['platform.name']))
    timeout, period = (args.get(x) for x in ['timeout', 'period'])
    print("Waiting...")
    while True:
        boot = get_boot(token, api, meta, lab)
        if boot:
            return boot
        if timeout and ((time.time() - start_time) > timeout):
            print("Timeout while waiting for boot")
            return None
        time.sleep(period)


def main(args):
    conf = configuration.get_config(args)
    api, token = (conf.get(x) for x in ['api', 'token'])

    if not token:
        raise Exception("No token provided")
    if not api:
        raise Exception("No KernelCI API URL provided")

    with open(args['submitted']) as jobs_file:
        jobs = json.load(jobs_file)

    lab = jobs['lab']
    all_passed = True
    boots = {}

    for job_def, job_id in jobs['jobs'].iteritems():
        with open(job_def) as job_yaml:
            job = yaml.safe_load(job_yaml)
        meta = job['metadata']
        boot = poll_boot(token, api, meta, lab, args)
        if not boot:
            print("Boot not found, skipping")
            all_passed = False
            continue

        keys = ['job', 'git_branch', 'kernel', 'arch', 'defconfig_full',
                'lab_name', 'board']
        name = '-'.join(boot[k] for k in keys)
        print("  id: {}, result: {}".format(
            boot['_id']['$oid'], boot['status']))
        print("  {}".format(name))
        if boot['status'] != 'PASS':
            all_passed = False
        boots[boot['_id']['$oid']] = boot

    output_path = args['output']
    print("Saving boot results in {}".format(output_path))
    with open(output_path, 'w') as output:
        json.dump(boots, output)

    sys.exit(0 if all_passed is True else 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Get boot results from KernelCI")
    parser.add_argument("--config",
                        help="path to KernelCI configuration file")
    parser.add_argument("--section", default="default",
                        help="section in the KernelCI config file")
    parser.add_argument("--token", help="KernelCI API Token")
    parser.add_argument("--api", help="KernelCI API URL")
    parser.add_argument("--lab", help="KernelCI Lab Name", required=True)
    parser.add_argument("--submitted", default="submitted.json",
                        help="path to JSON file with submitted jobs data")
    parser.add_argument("--output", default="boots.json",
                        help="path to JSON file to write the boot data")
    parser.add_argument("--timeout", default=0.0, type=float,
                        help="poll timeout")
    parser.add_argument("--period", default=10.0, type=float,
                        help="poll period in seconds")
    args = vars(parser.parse_args())
    main(args)
