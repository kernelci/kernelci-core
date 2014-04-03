#!/usr/bin/python

import xmlrpclib
import sys
import subprocess
import fnmatch
import os
import json
import time

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
        try:
            for job in submitted_jobs:
                status = server.scheduler.job_status(job)
                if status['job_status'] == 'Complete':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : pass'
                    submitted_jobs.pop(job, None)
                elif status['job_status'] == 'Incomplete':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : fail'
                    submitted_jobs.pop(job, None)
                else:
                    print str(job) + ' - ' + str(status['job_status'])
                if not submitted_jobs:
                    run = False
                    break
                else:
                    time.sleep(10)
        except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
            print e
            continue

def submit_jobs():
    global online_devices
    global offline_devices
    global online_device_types
    global offline_device_types
    try:
        print "Submitting Jobs to Server..."
        for job in job_map:
            with open(job, 'rb') as stream:
                job_data = stream.read()
            job_info = json.loads(job_data)
            # Check if target is online
            if 'target' in job_info:
                if job_info['target'] in offline_devices:
                    print "%s is OFFLINE skipping submission" % job_info['target']
                    print os.path.basename(job) + ': skip'
                else:
                    job_map[job] = server.scheduler.submit_job(job_data)
            elif 'device_type' in job_info:
                if job_info['device_type'] in offline_device_types:
                    print "All device types: %s are OFFLINE, skipping..." % job_info['target']
                    print os.path.basename(job) + ' : skip'
                else:
                    job_map[job] = server.scheduler.submit_job(job_data)
            else:
                print "Malformed JSON: No device_type or target present, skipping..."
                print os.path.basename(job) + ' : skip'
    except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
        print "ERROR!"
        print e

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
        if device_type['idle'] < device_type['offline']:
            offline_device_types.append(device_type['name'])
        else:
            online_device_types.append(device_type['name'])
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

def main(url, jobs):
    connect(url)
    retrieve_jobs(jobs)
    load_jobs()
    submit_jobs()
    poll_jobs()
    exit(0)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])