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

job_map = {}


def submit_jobs(connection, server, bundle_stream=None):
    online_devices, offline_devices = gather_devices(connection)
    online_device_types, offline_device_types = gather_device_types(connection)
    print "Submitting Jobs to Server..."
    for job in job_map:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
            job_info = yaml.load(job_data)
            # Check if request device(s) are available
            if 'device_type' in job_info:
                if job_info['device_type'] in offline_device_types:
                    print "All device types: %s are OFFLINE, skipping..." % job_info['device_type']
                    print os.path.basename(job) + ' : skip'
                elif job_info['device_type'] in online_device_types:
                    pass
                    print "Submitting job %s to device-type %s" % (job_info.get('job_name', 'unknown'), job_info['device_type'])
                    jobs = connection.scheduler.submit_job(job_data)
                    if isinstance(jobs, int):
                        jobs = str(jobs).split()
                    job_map[job] = jobs
                else:
                    print "No device-type available on server, skipping..."
                    print os.path.basename(job) + ' : skip'
            elif 'device_group' in job_info:
                print "Multinode Job Detected! Not supported yet :("
            elif 'vm_group' in job_info:
                print "VMGroup Job Detected! Not supported yet :("
            else:
                print "Should never get here - no idea what job type"
                print os.path.basename(job) + ' : skip'
        except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError, ValueError) as e:
            print "JSON VALIDATION ERROR!"
            print job
            print e
            continue


def load_jobs(top):
    for root, dirnames, filenames in os.walk(top):
        for filename in fnmatch.filter(filenames, '*.yaml'):
            job_map[os.path.join(root, filename)] = None


def retrieve_jobs(jobs):
    cmd = 'git clone %s' % jobs
    try:
        print "Cloning LAVA Jobs..."
        subprocess.check_output(cmd, shell=True)
        print "Clone Successful!"
        print "clone-jobs : pass"
    except subprocess.CalledProcessError as e:
        print "ERROR!"
        print "Unable to clone %s" % jobs
        print "clone-jobs : fail"
        exit(1)


def gather_devices(connection):
    online_devices = {}
    offline_devices = {}
    print "Gathering Devices..."
    all_devices = connection.scheduler.all_devices()
    for device in all_devices:
        if device[4]: #check if pipeline device
            if device[2] == 'offline':
                offline_devices[device[0]] = 1
            else:
                online_devices[device[0]] = 1
    print "Gathered Devices Successfully!"
    return online_devices, offline_devices


def gather_device_types(connection):
    online_device_types = {}
    offline_device_types = {}
    print "Gathering Device Types..."
    all_device_types = connection.scheduler.all_device_types()
    for device_type in all_device_types:
        # Only use dictionary data structures
        if isinstance(device_type, dict):
            # Retired
            if device_type['idle'] == 0 and device_type['busy'] == 0 and device_type['offline'] == 0:
                offline_device_types[device_type['name']] = 0
            # Running
            elif device_type['idle'] > 0 or device_type['busy'] > 0:
                online_device_types[device_type['name']] = device_type['idle'] + device_type['busy']
            # Offline
            else:
                offline_device_types[device_type['name']] = device_type['offline']
    print "Gathered Device Types Successfully!"
    return online_device_types, offline_device_types


def main(args):
    config = configuration.get_config(args)

    url = utils.validate_input(config.get("username"), config.get("token"), config.get("server"))
    connection = utils.connect(url)

    if config.get("repo"):
        retrieve_jobs(config.get("repo"))

    if config.get("jobs"):
        load_jobs(config.get("jobs"))
        print "Loading jobs from top folder " + str(config.get("jobs"))
    else:
        load_jobs(os.getcwd())

    submit_jobs(connection, config.get("server"))
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--jobs", help="absolute path to top jobs folder (default scans the whole cwd)")
    parser.add_argument("--username", help="username for the LAVA server")
    parser.add_argument("--token", help="token for LAVA server api")
    parser.add_argument("--server", help="server url for LAVA server")
    parser.add_argument("--repo", help="git repo for LAVA jobs")
    parser.add_argument("--timeout", type=int, default=-1, help="polling timeout in seconds. default is -1.")
    args = vars(parser.parse_args())
    main(args)
