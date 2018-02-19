#!/usr/bin/python
#
# Copyright (C) 2016, 2017 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
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

# Usage ./lava-v2-submit-jobs.py --username test --token xxxx --lab lab-name --jobs jobfolder

import os
import xmlrpclib
import yaml
import subprocess
import fnmatch
import time
import re
import argparse
import httplib
import json
import configparser

from lib import utils
from lib import configuration

DEVICE_ONLINE_STATUS = ['idle', 'running', 'reserved']
JOBS = {}
SUBMITTED = {}

def submit_jobs(connection):
    print "Fetching all devices from LAVA"
    all_devices = connection.scheduler.all_devices()
    print "Fetching all device-types from LAVA"
    all_device_types = connection.scheduler.all_device_types()

    result = True

    print "Submitting Jobs to Server..."
    for job in JOBS:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
            job_info = yaml.safe_load(job_data)
            # Check if request device(s) are available
            if 'device_type' in job_info:
                for device_type in all_device_types:
                    if device_type['name'] == job_info['device_type']:
                        if device_type_has_available(device_type, all_devices):
                            print "Submitting job %s to device-type %s" % (job_info.get('job_name', 'unknown'), job_info['device_type'])
                            job_id = connection.scheduler.submit_job(job_data)
                            SUBMITTED[job] = job_id
                        else:
                            print "Found device-type %s on server, but it had no available pipeline devices" % device_type['name']
            elif 'device_group' in job_info:
                print "Multinode Job Detected! Not supported yet :("
            elif 'vm_group' in job_info:
                print "VMGroup Job Detected! Not supported yet :("
            else:
                print "Should never get here - no idea what job type"
                print os.path.basename(job) + ' : skip'
        except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError, ValueError) as e:
            print "Job submission error!"
            print job
            print e
            result = False
            continue

    return result

def load_jobs(top):
    for root, dirnames, filenames in os.walk(top):
        for filename in fnmatch.filter(filenames, '*.yaml'):
            JOBS[os.path.join(root, filename)] = None

def device_type_has_available(device_type, all_devices):
    for device in all_devices:
        if device[1] == device_type['name']:
            if device[2].lower() in DEVICE_ONLINE_STATUS:
                try:
                    return device[4]
                except IndexError:
                    print "LAVA all_devices() XMLRPC does not support pipeline"
                    return False
    return False

def main(args):
    config = configuration.get_config(args)

    jobs_submitted = config.get('submitted')
    lab = config.get('lab')
    if jobs_submitted:
        if not lab:
            raise Exception("Lab name required when saving submitted jobs")
        if os.path.exists(jobs_submitted):
            os.unlink(jobs_submitted)

    if config.get("repo"):
        retrieve_jobs(config.get("repo"))

    jobs = config.get("jobs")
    print("Loading jobs from {}".format(jobs))
    load_jobs(jobs)

    if not JOBS:
        print("No jobs to submit")
        result = False
    else:
        start_time = time.time()
        labs_config = configparser.ConfigParser()
        labs_config.read('labs.ini')
        lava_api = labs_config[config.get("lab")]['api']
        print("LAVA API: {}".format(lava_api))
        url = utils.validate_input(config.get("username"),
                                   config.get("token"),
                                   lava_api)
        connection = utils.connect(url)
        result = submit_jobs(connection)
        if jobs_submitted and SUBMITTED:
            print("Saving submitted jobs data in {}".format(jobs_submitted))
            data = {
                'start_time': start_time,
                'lab': config.get('lab'),
                'jobs': {k: v for k, v in SUBMITTED.iteritems() if v},
            }
            with open(jobs_submitted, 'w') as json_file:
                json.dump(data, json_file)

    exit(0 if result is True else 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default",
                        help="section in the LAVA config file")
    parser.add_argument("--lab", help="KernelCI Lab Name")
    parser.add_argument("--jobs", required=True,
                        help="path to jobs directory (default is cwd)")
    parser.add_argument("--username", help="username for the LAVA server")
    parser.add_argument("--token", help="token for LAVA server api")
    parser.add_argument("--repo", help="git repo for LAVA jobs")
    parser.add_argument("--submitted",
                        help="path to JSON file to save submitted jobs data")
    args = vars(parser.parse_args())
    main(args)
