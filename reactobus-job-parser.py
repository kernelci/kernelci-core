#!/usr/bin/python
#
# Copyright (C) 2016, 2017 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
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

import yaml
import sys
import urllib2
import requests
import urlparse
import json
import time
import argparse
import os
from ConfigParser import SafeConfigParser
from lib import configuration, device_map

def push(method, url, data, headers):
    retry = True
    while retry:
        if method == 'POST':
            response = requests.post(url, data=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, data=data, headers=headers)
        else:
            print "ERROR: unsupported method"
            exit(1)
        if response.status_code != 500:
            retry = False
            print "OK"
        else:
            time.sleep(10)
            print response.content


def logfile_url(base, job):
    return ("%s/scheduler/job/%i/log_file/plain" % (base, job))


def results_url(base, job):
    return ("%s/results/%i/yaml" % (base, job))


def definition_url(base, job):
    return ("%s/scheduler/job/%i/definition/plain" % (base, job))


def base_url_from_topic(topic):
    if topic.startswith("http://") or topic.startswith("https://"):
        if topic.endswith(".testjob"):
            return topic[:-8]
        return topic
    else:
        bits = topic.split(".")
        if 'testjob' in bits:
            bits.remove('testjob')
        bits.reverse()
        url = "http://" + ".".join(bits)
        return url


def logfile_parse(logfile):
    final = []
    for line in logfile.splitlines():
        bits = yaml.load(line)[0]
        if bits['lvl'] == 'target':
            final.append(bits['msg'])
    return "\n".join(final)


def fetch(url):
    try:
        return urllib2.urlopen(url).read()
    except Exception as exc:
        print("ERROR Fetching: %s  -  %s" % (url,exc))
        return None

def read_jobinfo():
    data = ""
    for line in sys.stdin:
        data += line
    try:
        return yaml.load(data)
    except yaml.YAMLError as exc:
        print exc
        sys.exit(0)

def update_api(status, jobinfo, lab_url, lab_name, api_token, api_base):
    # http://lava.streamtester.net/scheduler/job/109/log_file/plain
    # http://lava.streamtester.net/results/109/yaml
    # http://lava.streamtester.net/results/109/metadata
    # http://lava.streamtester.net/scheduler/job/109/definition/plain
    job = int(jobinfo['job'])
    kernel_messages = []
    kernel_boot_time = 0
    boot_meta = {}

    logfile_plain = logfile_parse(fetch(logfile_url(lab_url, job)))
    results_yaml = fetch(results_url(lab_url, job))
    definition_yaml = fetch(definition_url(lab_url, job))
    jobdef = yaml.load(definition_yaml)
    metadata = jobdef['metadata']
    if results_yaml:
        results = yaml.load(results_yaml)
    else:
        results = {}
    boot_result = 'UNTRIED'
    if status == 'complete':
        boot_result = 'PASS'
    elif status == 'cancelled':
        boot_result = 'OFFLINE'
    else:
        boot_result = 'FAIL'
    for result in results:
        if result['name'] == 'auto-login-action':
            if 'metadata' in result:
                if 'extra' in result['metadata']:
                    if 'fail' in result['metadata']['extra']:
                        for fail in result['metadata']['extra']['fail']:
                            kernel_messages.append(fail['message'])
            kernel_boot_time = result['metadata']['duration']
        if result['name'] == 'bootloader-overlay':
            if 'metadata' in result:
                if 'extra' in result['metadata']:
                    for extra in result['metadata']['extra']:
                        if 'kernel_addr' in extra:
                            boot_meta['loadaddr'] = extra.get('kernel_addr', None)
                        if 'ramdisk_addr' in extra:
                            boot_meta['initrd_addr'] = extra.get('ramdisk_addr', None)
                        if 'dtb_addr' in extra:
                            boot_meta['dtb_addr'] = extra.get('dtb_addr', None)

    boot_meta['lab_name'] = lab_name
    boot_meta['board_instance'] = jobinfo['device']
    boot_meta['retries'] = 0
    boot_meta['boot_log'] = "%s-lava-boot-log-plain.txt" % job
    boot_meta['boot_log_html'] = ""
    boot_meta['version'] = '1.1'
    boot_meta['arch'] = metadata['job.arch']
    boot_meta['defconfig'] = metadata['kernel.defconfig_base']
    boot_meta['defconfig_full'] = metadata['kernel.defconfig']
    if metadata['platform.dtb_short'] in device_map:
        if 'mach' in device_map[metadata['platform.dtb_short']][0]:
            boot_meta['mach'] = device_map[metadata['platform.dtb_short']][0]['mach']
    boot_meta['kernel'] = metadata['kernel.version']
    boot_meta['job'] = metadata['kernel.tree']
    boot_meta['board'] = metadata['device.type']
    boot_meta['boot_result'] = boot_result
    if boot_result == 'FAIL' or boot_result == 'OFFLINE':
        boot_meta['boot_result_description'] = 'Unknown Error: platform failed to boot'
    boot_meta['boot_time'] = kernel_boot_time
    if kernel_messages:
        boot_meta['boot_warnings'] = len(kernel_messages)
    boot_meta['dtb'] = metadata['platform.dtb']
    boot_meta['endian'] = metadata['kernel.endian']
    boot_meta['fastboot'] = metadata['platform.fastboot']
    boot_meta['initrd'] = metadata['job.initrd_url']
    boot_meta['kernel_image'] = metadata['job.kernel_image']
    boot_meta['git_branch'] = metadata['git.branch']
    boot_meta['git_commit'] = metadata['git.commit']
    boot_meta['git_describe'] = metadata['git.describe']
    print boot_meta
    print 'Sending boot result to %s for %s' % (api_base, metadata['device.type'])
    headers = {
        'Authorization': api_token,
        'Content-Type': 'application/json'
    }
    api_url = urlparse.urljoin(api_base, '/boot')
    push('POST', api_url, data=json.dumps(boot_meta), headers=headers)


    headers = {
        'Authorization': api_token,
        'Content-Type': 'text/plain'
    }
    print 'Uploading text version of boot log'
    api_url = urlparse.urljoin(api_base, '/upload/%s/%s/%s/%s/%s' % (metadata['kernel.tree'],
                                                                     metadata['kernel.version'],
                                                                     metadata['kernel.arch_defconfig'],
                                                                     lab_name,
                                                                     boot_meta['boot_log']))
    push('PUT', api_url, data=logfile_plain, headers=headers)

def lab_from_config(lab_url, config_file):
    parser = SafeConfigParser()
    parser.read(os.path.expanduser(config_file))
    for section_name in parser.sections():
        for item, value in parser.items(section_name):
            if item == 'url':
                if value == lab_url:
                    return section_name, parser.get(section_name, 'api-token')
    print("Could not find lab config for %s" % lab_url)
    sys.exit(1)

def main(args):
    lab_url = base_url_from_topic(args.topic)
    lab_name, api_token = lab_from_config(lab_url, args.config)
    jobinfo = read_jobinfo()
    status = jobinfo['status'].lower()
    if status in ["complete", "incomplete", "cancelled"]:
        update_api(status, jobinfo, lab_url, lab_name, api_token, args.api)
    else:
        print("job still running")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="zmq topic (usually lab url)", required=True)
    parser.add_argument("--api", help="Kernel CI API URL", default="https//api.kernelci.org")
    parser.add_argument("--config", help="Kernel CI labs config file (~/kernelci-labs.cfg)", default="~/kernelci-labs.cfg")
    args = parser.parse_args()
    main(args)
