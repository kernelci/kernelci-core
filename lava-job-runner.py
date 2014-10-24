#!/usr/bin/python
# <variable> = required
# [variable] = optional
# Usage ./lava-job-runner.py <username> <token> <lava_server_url> [job_repo] [bundle_stream]

import xmlrpclib
import subprocess
import fnmatch
import os
import json
import time
import re
import urlparse
import argparse

job_map = {}


def report(jobs):
    for job in jobs:
        print str(job) + ' ' + jobs[job]


def poll_jobs(connection):
    run = True
    submitted_jobs = {}
    finished_jobs = {}

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
                    finished_jobs[job] = 'PASS'
                    submitted_jobs.pop(job, None)
                    break
                elif status['job_status'] == 'Incomplete' or status['job_status'] == 'Canceled' or status['job_status'] == 'Canceling':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : fail'
                    # Pop
                    finished_jobs[job] = 'FAIL'
                    submitted_jobs.pop(job, None)
                    break
                else:
                    print str(job) + ' - ' + str(status['job_status'])
                    time.sleep(10)
            except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
                print "POLLING ERROR!"
                print e
                continue

    return finished_jobs


def submit_jobs(connection, server, bundle_stream):
    online_devices, offline_devices = gather_devices(connection)
    online_device_types, offline_device_types = gather_device_types(connection)
    print "Submitting Jobs to Server..."
    for job in job_map:
        try:
            with open(job, 'rb') as stream:
                job_data = stream.read()
                # Injection
                if bundle_stream is not None:
                    job_data = re.sub('LAVA_SERVER', server, job_data)
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
                        server_has_required_devices = False
                        print os.path.basename(job) + ' : skip'
                        break
                    elif groups['device_type'] in online_device_types:
                        if groups['count'] > multinode_online_device_types[groups['device_type']]:
                            print "Server does not have enough online devices to submit job!"
                            print os.path.basename(job) + ' : skip'
                            server_has_required_devices = False
                            break
                        elif groups['count'] <= multinode_online_device_types[groups['device_type']]:
                            print "Server has enough devices for this group!"
                            multinode_online_device_types[groups['device_type']] = multinode_online_device_types[groups['device_type']] - groups['count']
                        else:
                            print "Should never get here!"
                            print os.path.basename(job) + ' : skip'
                            server_has_required_devices = False
                            break
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


def validate_input(username, token, server):
    url = urlparse.urlparse(server)
    if url.path.find('RPC2') == -1:
        print "LAVA Server URL must end with /RPC2"
        exit(1)
    return url.scheme + '://' + username + ':' + token + '@' + url.netloc + url.path


def main(args):

    url = validate_input(args.username, args.token, args.server)
    connection = connect(url)
    if args.repo:
        retrieve_jobs(args.repo)
    load_jobs()
    if args.stream:
        submit_jobs(connection, args.server, args.stream)
    else:
        submit_jobs(connection, args.server, bundle_stream=None)
    if args.poll:
        jobs = poll_jobs(connection)
        if args.report:
            report(jobs)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="username for the LAVA server")
    parser.add_argument("token", help="token for LAVA server api")
    parser.add_argument("server", help="server url for LAVA server")
    parser.add_argument("--stream", help="bundle stream for LAVA server")
    parser.add_argument("--repo", help="git repo for LAVA jobs")
    parser.add_argument("--poll", action='store_true', help="poll the submitted LAVA jobs")
    parser.add_argument("--report", action='store_true', help="report on the submitted LAVA jobs")
    args = parser.parse_args()
    main(args)