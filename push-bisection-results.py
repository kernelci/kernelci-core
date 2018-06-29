#!/usr/bin/env python

# Copyright (C) 2018 Collabora Limited
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
import requests
import subprocess
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import urlparse
from lib import configuration, device_map


def git_summary(repo, revision):
    return subprocess.check_output(
        "cd {}; git show --oneline {} | head -n1".format(repo, revision),
        shell=True).strip()


def git_cmd(repo, cmd):
    return subprocess.check_output(
        "cd {}; git {}".format(repo, cmd),
        shell=True).strip()


def git_bisect_log(repo):
    p = subprocess.Popen("cd {}; git bisect log".format(repo),
                         shell=True, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    return list(l.strip() for l in StringIO(stdout).readlines())


def upload_log(args, upload_path, log_file_name, token, api):
    kdir = args['kdir']
    log_data = {
        'show': git_cmd(kdir, 'show refs/bisect/bad'),
        'log': git_bisect_log(kdir),
    }
    headers = {
        'Authorization': token,
    }
    data = {
        'path': upload_path,
    }
    files = {
        ('file1', (log_file_name, StringIO(json.dumps(log_data, indent=4)))),
    }
    url = urlparse.urljoin(api, '/upload')
    response = requests.post(url, headers=headers, data=data, files=files)
    response.raise_for_status()


def send_result(args, log_file_name, token, api):
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }
    data_map = {
        'type': 'type',
        'arch': 'arch',
        'job': 'tree',
        'kernel': 'kernel',
        'git_branch': 'branch',
        'defconfig_full': 'defconfig',
        'lab_name': 'lab',
        'device_type': 'target',
        'good_commit': 'good',
        'bad_commit': 'bad',
    }
    data = {k: args[v] for k, v in data_map.iteritems()}
    kdir = args['kdir']
    data.update({
        'log': log_file_name,
        'good_summary': git_summary(kdir, args['good']),
        'bad_summary': git_summary(kdir, args['bad']),
        'found_summary': git_summary(kdir, 'refs/bisect/bad'),
        'checks': { check: args[check] for check in [
            'verify',
            'revert',
        ]},
    })
    url = urlparse.urljoin(api, '/bisect')
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def send_report(args, log_file_name, token, api):
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }
    data_map = {
        'type': 'type',
        'job': 'tree',
        'kernel': 'kernel',
        'git_branch': 'branch',
        'arch': 'arch',
        'defconfig_full': 'defconfig',
        'lab_name': 'lab',
        'device_type': 'target',
        'good_commit': 'good',
        'bad_commit': 'bad',
        'subject': 'subject',
    }
    data = {k: args[v] for k, v in data_map.iteritems()}
    data.update({
        'report_type': 'bisect',
        'log': log_file_name,
        'format': ['txt', 'html'],
        'send_to': args['to'].split(' '),
    })
    url = urlparse.urljoin(api, '/send')
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def main(args):
    config = configuration.get_config(args)
    token = config.get('token')
    api = config.get('api')

    if not token:
        raise Exception("No KernelCI API token provided")
    if not api:
        raise Exception("No KernelCI API URL provided")

    upload_path = '/'.join(args[k] for k in [
        'tree', 'branch', 'kernel', 'arch', 'defconfig', 'lab'])
    log_file_name = 'bisect-{}.json'.format(args['target'])

    print("Uploading bisect log: {}".format(upload_path))
    upload_log(args, upload_path, log_file_name, token, api)

    print("Sending bisection results")
    send_result(args, log_file_name, token, api)

    print("Sending bisection report email")
    send_report(args, log_file_name, token, api)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Push automated bisection results to the KernelCI backend API")
    parser.add_argument("--config",
                        help="path to KernelCI configuration file")
    parser.add_argument("--token",
                        help="KernelCI API Token")
    parser.add_argument("--api",
                        help="KernelCI API URL")
    parser.add_argument("--lab", required=True,
                        help="KernelCI lab name")
    parser.add_argument("--arch", required=True,
                        help="CPU architecture")
    parser.add_argument("--defconfig", required=True,
                        help="full defconfig")
    parser.add_argument("--target", required=True,
                        help="target device type")
    parser.add_argument("--tree", required=True,
                        help="kernel tree name")
    parser.add_argument("--kernel", required=True,
                        help="kernel identifier")
    parser.add_argument("--branch", required=True,
                        help="git branch")
    parser.add_argument("--good", required=True,
                        help="good commit sha")
    parser.add_argument("--bad", required=True,
                        help="bad commit sha")
    parser.add_argument("--verify", required=True,
                        help="verified status")
    parser.add_argument("--revert", default="SKIPPED",
                        help="revert check status")
    parser.add_argument("--type", default='boot',
                        help="bisection type")
    parser.add_argument("--kdir", required=True,
                        help="path to the kernel directory")
    parser.add_argument("--subject", required=True,
                        help="email report subject")
    parser.add_argument("--to", required=True,
                        help="email recipients")
    args = vars(parser.parse_args())
    main(args)
