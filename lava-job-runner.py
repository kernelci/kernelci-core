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
import shutil

job_map = {}


def kreport(connection, jobs, duration):
    results_directory = os.getcwd() + '/results'
    results = {}
    mkdir(results_directory)
    for job_id in jobs:
        # Retrieve job details
        job_details = connection.scheduler.job_details(job_id)
        if job_details['requested_device_type_id']:
            device_type = job_details['requested_device_type_id']
        if job_details['description']:
            job_name = job_details['description']
        result = jobs[job_id]['result']
        bundle = jobs[job_id]['bundle']
        # Retrieve the log file
        binary_job_file = connection.scheduler.job_output(job_id)
        job_file = str(binary_job_file)
        # Retrieve bundle
        if bundle is not None:
            json_bundle = connection.dashboard.get(bundle)
            bundle_data = json.loads(json_bundle['content'])
            bundle_attributes =  bundle_data['test_runs'][0]['attributes']
            boot_meta = {}
            kernel_defconfig = None
            kernel_version = None
            kernel_boot_time = None
            kernel_tree = None
            kernel_image = None
            kernel_addr = None
            initrd_addr = None
            dtb_addr = None
            dtb_append = None
            if in_bundle_attributes(bundle_attributes, 'kernel.defconfig'):
                kernel_defconfig = bundle_attributes['kernel.defconfig']
            if in_bundle_attributes(bundle_attributes, 'kernel.version'):
                kernel_version = bundle_attributes['kernel.version']
            if in_bundle_attributes(bundle_attributes, 'kernel-boot-time'):
                kernel_boot_time = bundle_attributes['kernel-boot-time']
            if in_bundle_attributes(bundle_attributes, 'kernel.tree'):
                kernel_tree = bundle_attributes['kernel.tree']
            if in_bundle_attributes(bundle_attributes, 'kernel-image'):
                kernel_image = bundle_attributes['kernel-image']
            if in_bundle_attributes(bundle_attributes, 'kernel-addr'):
                kernel_addr = bundle_attributes['kernel-addr']
            if in_bundle_attributes(bundle_attributes, 'initrd-addr'):
                initrd_addr = bundle_attributes['initrd-addr']
            if in_bundle_attributes(bundle_attributes, 'dtb-addr'):
                dtb_addr = bundle_attributes['dtb-addr']
            if in_bundle_attributes(bundle_attributes, 'dtb-append'):
                dtb_append = bundle_attributes['dtb-append']
        # Record the boot log and result
        # TODO: Will need to map device_types to dashboard device types
        if kernel_defconfig and device_type and kernel_boot_time and result:
            print 'Creating boot log for %s' % device_type
            log = 'boot-%s.log' % device_type
            directory = os.path.join(results_directory, kernel_defconfig)
            mkdir(directory)
            write_file(job_file, log, directory)
            if results.has_key(kernel_defconfig):
                results[kernel_defconfig].append({'device_type': device_type, 'kernel_boot_time': kernel_boot_time, 'result': result})
            else:
                results[kernel_defconfig] = [{'device_type': device_type, 'kernel_boot_time': kernel_boot_time, 'result': result}]
            # Create JSON format boot metadata
            print 'Creating JSON format boot metadata'
            boot_meta['boot_log'] = log
            # TODO: Fix this
            boot_meta['boot_log_html'] = None
            boot_meta['boot_result'] = result
            boot_meta['boot_time'] = kernel_boot_time
            # TODO: Fix this
            boot_meta['boot_warnings'] = None
            # TODO: Fix this
            boot_meta['dtb'] = None
            boot_meta['dtb_addr'] = dtb_addr
            boot_meta['dtb_append'] = dtb_append
            # TODO: Fix this
            boot_meta['endian'] = None
            # TODO: Fix this
            boot_meta['initrd'] = None
            boot_meta['initrd_addr'] = initrd_addr
            boot_meta['kernel_image'] = kernel_image
            boot_meta['loadaddr'] = kernel_addr
            json_file = 'boot-%s.json' % device_type
            json_path = os.path.join(directory, json_file)
            boot_json_f = open(json_path, 'w')
            json.dump(boot_meta, boot_json_f, indent=4, sort_keys=True)
            boot_json_f.close()

    if results and kernel_tree and kernel_version:
        print 'Creating boot summary for %s' % kernel_version
        log = '%s-boot-report.log' % kernel_version
        with open(os.path.join(results_directory, log), 'a') as f:
            f.write('Status Dashboard: http://status.armcloud.us/boot/all/job/%s/kernel/%s/\n' % (kernel_tree, kernel_version))
            f.write('\n')
            f.write('Total duration: %.2f seconds\n' % duration)
            f.write('Tree/Branch: %s\n' % kernel_tree)
            f.write('Git describe: %s\n' % kernel_version)
            f.write('\n')
            f.write('Full Report:\n')
            for defconfig, results_list in results.items():
                f.write('\n')
                f.write(defconfig)
                f.write('\n')
                for result in results_list:
                    f.write('    %s   %ss   %s\n' % (result['device_type'], result['kernel_boot_time'], result['result']))

def write_file(file, name, directory):
    with open(os.path.join(directory, name), 'w') as f:
        f.write(file)

def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)

def in_bundle_attributes(bundle_atrributes, key):
    if key in bundle_atrributes:
        return True
    else:
        return False

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
                    if status['bundle_sha1']:
                        finished_jobs[job] = {'result': 'PASS', 'bundle': status['bundle_sha1']}
                    else:
                        finished_jobs[job] = {'result': 'PASS', 'bundle': None}
                    submitted_jobs.pop(job, None)
                    break
                elif status['job_status'] == 'Incomplete' or status['job_status'] == 'Canceled' or status['job_status'] == 'Canceling':
                    print 'job-id-' + str(job) + '-' + os.path.basename(submitted_jobs[job]) + ' : fail'
                    # Pop
                    if status['bundle_sha1']:
                        finished_jobs[job] = {'result': 'FAIL', 'bundle': status['bundle_sha1']}
                    else:
                        finished_jobs[job] = {'result': 'FAIL', 'bundle': None}
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
    start_time = time.time()
    if args.stream:
        submit_jobs(connection, args.server, args.stream)
    else:
        submit_jobs(connection, args.server, bundle_stream=None)
    if args.poll:
        jobs = poll_jobs(connection)
        end_time = time.time()
        duration = end_time - start_time
        if args.kreport:
            kreport(connection, jobs, duration)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="username for the LAVA server")
    parser.add_argument("token", help="token for LAVA server api")
    parser.add_argument("server", help="server url for LAVA server")
    parser.add_argument("--stream", help="bundle stream for LAVA server")
    parser.add_argument("--repo", help="git repo for LAVA jobs")
    parser.add_argument("--poll", action='store_true', help="poll the submitted LAVA jobs")
    parser.add_argument("--kreport", action='store_true', help="kernel-ci report for the submitted LAVA jobs")
    args = parser.parse_args()
    main(args)