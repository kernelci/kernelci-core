#!/usr/bin/python

import xmlrpclib
import sys
import subprocess
import fnmatch
import os
import json
import time
import re

server = None
online_device_types = []
offline_device_types = []
online_devices = []
offline_devices = []
job_map = {}

def poll_jobs():
    run = True
    submitted_jobs = {}

    for job in job_map:
        if job_map[job] is not None:
            submitted_jobs[job_map[job]] = job

    while run:
        for job in submitted_jobs:
            try:
                status = server.scheduler.job_status(job)
                if status['job_status'] == 'Complete':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : pass'
                    submitted_jobs.pop(job, None)
                    break
                elif status['job_status'] == 'Incomplete':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : fail'
                    submitted_jobs.pop(job, None)
                    break
                else:
                    print str(job) + ' - ' + str(status['job_status'])
                if not submitted_jobs:
                    run = False
                    break
                else:
                    time.sleep(10)
            except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
                print "POLLING ERROR!"
                print e
                continue

def submit_jobs(lava_server, bundle_stream):
    global online_devices
    global offline_devices
    global online_device_types
    global offline_device_types
    print "Submitting Jobs to Server..."
    for job in job_map:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
                job_data = re.sub('LAVA_SERVER', lava_server, job_data)
                job_data = re.sub('BUNDLE_STREAM', bundle_stream, job_data)
            job_info = json.loads(job_data)
            # Check if request device(s) are available
            if 'target' in job_info:
                if job_info['target'] in offline_devices:
                    print "%s is OFFLINE skipping submission" % job_info['target']
                    print os.path.basename(job) + ': skip'
                elif job_info['target'] in online_devices:
                    job_map[job] = server.scheduler.submit_job(job_data)
                else:
                    print "No target available on server, skipping..."
                    print os.path.basename(job) + ' : skip'
            elif 'device_type' in job_info:
                if job_info['device_type'] in offline_device_types:
                    print "All device types: %s are OFFLINE, skipping..." % job_info['device_type']
                    print os.path.basename(job) + ' : skip'
                elif job_info['device_type'] in online_device_types:
                    job_map[job] = server.scheduler.submit_job(job_data)
                else:
                    print "No device-type available on server, skipping..."
                    print os.path.basename(job) + ' : skip'
            else:
                print "Multinode Job not supported, skipping..."
                print os.path.basename(job) + ' : skip'
        except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError, ValueError) as e:
            print "JSON VALIDATION ERROR!"
            print job
            print e
            continue

def load_jobs():
    top = os.getcwd()
    for root, dirnames, filenames in os.walk(top):
        for filename in fnmatch.filter(filenames, '*.json'):
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

def gather_devices():
    global online_devices
    global offline_devices
    print "Gathering Devices..."
    all_devices = server.scheduler.all_devices()
    for device in all_devices:
        if device[2] == 'offline':
            offline_devices.append(device[0])
        else:
            online_devices.append(device[0])
    print "Gathered Devices Successfully!"

def gather_device_types():
    global online_device_types
    global offline_device_types
    print "Gathering Device Types..."
    all_device_types = server.scheduler.all_device_types()
    for device_type in all_device_types:
        # Retired
        if device_type['idle'] == 0 and device_type['busy'] == 0 and device_type['offline'] == 0:
            offline_device_types.append(device_type['name'])
        # Running
        elif device_type['idle'] > 0 or device_type['busy'] > 0:
            online_device_types.append(device_type['name'])
        # Offline
        else:
            offline_device_types.append(device_type['name'])
    print "Gathered Device Types Successfully!"

def connect(url):
    try:
        print "Connecting to Server..."
        global server
        global online_device_types
        global offline_device_types
        server = xmlrpclib.ServerProxy(url)
        gather_device_types()
        gather_devices()
        print "Connection Successful!"
        print "connect-to-server : pass"
    except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
        print "ERROR!"
        print "Unable to connect to %s" % url
        print "The URL should be in the form http(s)://<user>:<token>@hostname/RPC2"
        print "connect-to-server : fail"
        print e
        exit(1)

def main(url, jobs, lava_server, bundle_stream):
    connect(url)
    retrieve_jobs(jobs)
    load_jobs()
    submit_jobs(lava_server, bundle_stream)
    poll_jobs()
    exit(0)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])