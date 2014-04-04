#!/usr/bin/python
# <variable> = required
# [variable] = optional
# Usage ./lava-job-runner.py <username> <token> <lava_server_url> <job_repo> [bundle_stream]

import xmlrpclib
import sys
import subprocess
import fnmatch
import os
import json
import time
import re
import urlparse

job_map = {}


def report():
    pass


def poll_jobs(connection):
    run = True
    submitted_jobs = {}

    for job in job_map:
        if job_map[job] is not None:
            # Push
            submitted_jobs[job_map[job]] = job

    while run:
        if not submitted_jobs:
            run = False
            break
        for job in submitted_jobs:
            try:
                status = connection.scheduler.job_status(job)
                if status['job_status'] == 'Complete':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : pass'
                    # Pop
                    submitted_jobs.pop(job, None)
                    break
                elif status['job_status'] == 'Incomplete' or status['job_status'] == 'Canceled' or status['job_status'] == 'Canceling':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : fail'
                    # Pop
                    submitted_jobs.pop(job, None)
                    break
                else:
                    print str(job) + ' - ' + str(status['job_status'])
                    time.sleep(10)
            except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
                print "POLLING ERROR!"
                print e
                continue


def submit_jobs(connection, lava_server, bundle_stream):
    online_devices, offline_devices = gather_devices(connection)
    online_device_types, offline_device_types = gather_device_types(connection)
    print "Submitting Jobs to Server..."
    for job in job_map:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
                # Injection
                job_data = re.sub('LAVA_SERVER', lava_server, job_data)
                job_data = re.sub('BUNDLE_STREAM', bundle_stream, job_data)
            job_info = json.loads(job_data)
            # Check if request device(s) are available
            if 'target' in job_info:
                if job_info['target'] in offline_devices:
                    print "%s is OFFLINE skipping submission" % job_info['target']
                    print os.path.basename(job) + ': skip'
                elif job_info['target'] in online_devices:
                    pass
                    job_map[job] = connection.scheduler.submit_job(job_data)
                else:
                    print "No target available on server, skipping..."
                    print os.path.basename(job) + ' : skip'
            elif 'device_type' in job_info:
                if job_info['device_type'] in offline_device_types:
                    print "All device types: %s are OFFLINE, skipping..." % job_info['device_type']
                    print os.path.basename(job) + ' : skip'
                elif job_info['device_type'] in online_device_types:
                    pass
                    job_map[job] = connection.scheduler.submit_job(job_data)
                else:
                    print "No device-type available on server, skipping..."
                    print os.path.basename(job) + ' : skip'
            elif 'device_group' in job_info:
                print "Multinode Job Detected! Checking if required devices are available..."
                multinode_online_device_types = online_device_types
                server_has_required_devices = True
                for groups in job_info['device_group']:
                    if groups['device_type'] in offline_device_types:
                        print "All device types: %s are OFFLINE, skipping..." % groups['device_type']
                        print os.path.basename(job) + ' : skip'
                    elif groups['device_type'] in online_device_types:
                        if groups['count'] > multinode_online_device_types[groups['device_type']]:
                            print "Server does not have enough online devices to submit job!"
                            print os.path.basename(job) + ' : skip'
                            server_has_required_devices = False
                        elif groups['count'] <= multinode_online_device_types[groups['device_type']]:
                            print "Server has enough devices for this group!"
                            multinode_online_device_types[groups['device_type']] = multinode_online_device_types[groups['device_type']] - groups['count']
                        else:
                            print "Should never get here!"
                            print os.path.basename(job) + ' : skip'
                            server_has_required_devices = False
                    else:
                        print "No device-type available on server, skipping..."
                        print os.path.basename(job) + ' : skip'
                if server_has_required_devices:
                    print "Submitting Multinode Job!"
                    job_map[job] = connection.scheduler.submit_job(job_data)[0]
            else:
                print "Should never get here"
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


def gather_devices(connection):
    online_devices = {}
    offline_devices = {}
    print "Gathering Devices..."
    all_devices = connection.scheduler.all_devices()
    for device in all_devices:
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


def connect(url):
    try:
        print "Connecting to Server..."
        connection = xmlrpclib.ServerProxy(url)

        print "Connection Successful!"
        print "connect-to-server : pass"
        return connection
    except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
        print "CONNECTION ERROR!"
        print "Unable to connect to %s" % url
        print e
        print "connect-to-server : fail"
        exit(1)


def validate_input(username, token, lava_server):
    url = urlparse.urlparse(lava_server)
    if url.path.find('RPC2') == -1:
        print "LAVA Server URL must end with /RPC2"
        exit(1)
    return url.scheme + '://' + username + ':' + token + '@' + url.netloc + url.path


def main(username, token, lava_server, job_repo, bundle_stream='/anonymous/lava-functional-tests/'):
    url = validate_input(username, token, lava_server)
    connection = connect(url)
    retrieve_jobs(job_repo)
    load_jobs()
    submit_jobs(connection, lava_server, bundle_stream)
    poll_jobs(connection)
    report()
    exit(0)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])