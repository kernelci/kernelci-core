#!/usr/bin/python
# Usage ./lava-v2-submit-jobs.py --username test --token xxxx --server http://server/RPC2 --jobs jobfolder

import os
import xmlrpclib
import yaml
import subprocess
import fnmatch
import time
import re
import argparse
import httplib

from lib import utils
from lib import configuration

DEVICE_ONLINE_STATUS = ['idle', 'running', 'reserved']
JOBS = {}

def submit_jobs(connection):
    print "Fetching all devices from LAVA"
    all_devices = connection.scheduler.all_devices()
    print "Fetching all device-types from LAVA"
    all_device_types = connection.scheduler.all_device_types()

    print "Submitting Jobs to Server..."
    for job in JOBS:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
            job_info = yaml.load(job_data)
            # Check if request device(s) are available
            if 'device_type' in job_info:
                for device_type in all_device_types:
                    if device_type['name'] == job_info['device_type']:
                        if device_type_has_available(device_type, all_devices):
                            print "Submitting job %s to device-type %s" % (job_info.get('job_name', 'unknown'), job_info['device_type'])
                            connection.scheduler.submit_job(job_data)
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
            continue

def load_jobs(top):
    for root, dirnames, filenames in os.walk(top):
        for filename in fnmatch.filter(filenames, '*.yaml'):
            JOBS[os.path.join(root, filename)] = None

def device_type_has_available(device_type, all_devices):
    for device in all_devices:
        if device[1] == device_type['name']:
            if device[2] in DEVICE_ONLINE_STATUS:
                try:
                    return device[4]
                except IndexError:
                    print "LAVA all_devices() XMLRPC does not support pipeline"
                    return False
    return False

def main(args):
    config = configuration.get_config(args)

    if config.get("repo"):
        retrieve_jobs(config.get("repo"))

    jobs = config.get("jobs")
    print("Loading jobs from {}".format(jobs))
    load_jobs(jobs)

    if JOBS:
        start_time = time.time()
        url = utils.validate_input(config.get("username"), config.get("token"),
                                   config.get("server"))
        connection = utils.connect(url)
        submit_jobs(connection)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default",
                        help="section in the LAVA config file")
    parser.add_argument("--jobs", required=True,
                        help="path to jobs directory (default is cwd)")
    parser.add_argument("--username", help="username for the LAVA server")
    parser.add_argument("--token", help="token for LAVA server api")
    parser.add_argument("--server", help="server url for LAVA server")
    parser.add_argument("--repo", help="git repo for LAVA jobs")
    args = vars(parser.parse_args())
    main(args)
