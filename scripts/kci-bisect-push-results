#!/usr/bin/env python3

# Copyright (C) 2018, 2019 Collabora Limited
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
import re
import requests
import subprocess
try:
    from io import StringIO
except ImportError:
    from io import StringIO
import urllib.parse

RE_ADDR = r'.*@.*\.[a-z]+'
RE_TRAILER = re.compile(r'^(?P<tag>[A-Z][a-z-]*)\: (?P<value>.*)$')
RE_EMAIL = re.compile(r'^(?P<name>.*)(?P<email><{}>)'.format(RE_ADDR))
RE_MAILING_LIST = re.compile(r'^(?P<email>{}) \('.format(RE_ADDR))


def git_cmd(repo, cmd):
    return subprocess.check_output(
        "cd {}; git {}".format(repo, cmd),
        shell=True).decode().strip()


def git_summary(repo, revision):
    return git_cmd(repo, "show --oneline {} | head -n1".format(revision))


def git_bisect_log(repo):
    p = subprocess.Popen("cd {}; git bisect log".format(repo),
                         shell=True, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    return list(ln.strip() for ln in StringIO(stdout.decode()).readlines())


def git_show_fmt(repo, revision, fmt):
    return git_cmd(
        repo,
        "show {} -s --pretty=format:'{}'".format(revision, fmt))


def name_address(data):
    name, address = (data.get(k, '').strip() for k in ['name', 'email'])
    if name:
        address = ' '.join([name, address])
    return address


def git_maintainers(kdir, revision):
    maintainers = set()
    p = subprocess.Popen(
        "cd {}; git show {} --pretty=format:%b".format(kdir, revision),
        shell=True, stdout=subprocess.PIPE)
    body = p.communicate()[0]
    p = subprocess.Popen(
        "cd {}; ./scripts/get_maintainer.pl --nogit".format(kdir),
        shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    raw = p.communicate(input=body)[0].decode()
    for ln in raw.split('\n'):
        m = RE_EMAIL.match(ln) or RE_MAILING_LIST.match(ln)
        if m:
            maintainers.add(name_address(m.groupdict()))
    return list(maintainers)


def git_people(kdir, revision):
    people = {
        'maintainers': git_maintainers(kdir, revision),
        'author': [git_show_fmt(kdir, revision, '%an <%ae>')],
        'committer': [git_show_fmt(kdir, revision, '%cn <%ce>')],
        'Acked-by': [],
        'Reported-by': [],
        'Reviewed-by': [],
        'Signed-off-by': [],
        'Tested-by': [],
    }
    body = git_show_fmt(kdir, revision, '%b')

    for ln in body.split('\n'):
        m = RE_TRAILER.match(ln)
        if m:
            md = m.groupdict()
            tag, value = (md[k] for k in ['tag', 'value'])
            if tag in people:
                e = RE_EMAIL.match(value)
                if e:
                    people[tag].append(name_address(e.groupdict()))

    return people


def add_git_recipients(kdir, revision, to, cc):
    recipients_map = {
        'author': to,
        'committer': cc,
        'maintainers': cc,
        'Acked-by': to,
        'Reported-by': to,
        'Reviewed-by': to,
        'Signed-off-by': to,
        'Tested-by': to,
    }
    people = git_people(kdir, revision)

    for category, entries in people.items():
        recip = recipients_map[category]
        for e in entries:
            recip.add(e)


def checks_dict(args):
    return {check: getattr(args, check) for check in [
        'verify',
        'revert',
    ]}


def upload_log(args, upload_path, log_file_name, token, api):
    kdir = args.kdir
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
    url = urllib.parse.urljoin(api, '/upload')
    response = requests.post(url, headers=headers, data=data, files=files)
    response.raise_for_status()


def send_result(args, log_file_name, token, api):
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }
    data_map = {
        'arch': 'arch',
        'job': 'tree',
        'kernel': 'kernel',
        'git_branch': 'branch',
        'defconfig_full': 'defconfig',
        'build_environment': 'build_environment',
        'lab_name': 'lab',
        'device_type': 'target',
        'test_case_path': 'test_case',
        'good_commit': 'good',
        'bad_commit': 'bad',
    }
    data = {k: getattr(args, v) for k, v in data_map.items()}
    kdir = args.kdir
    data.update({
        'type': args.bisect_type,
        'log': log_file_name,
        'good_summary': git_summary(kdir, args.good),
        'bad_summary': git_summary(kdir, args.bad),
        'found_summary': git_summary(kdir, 'refs/bisect/bad'),
        'checks': checks_dict(args),
    })
    url = urllib.parse.urljoin(api, '/bisect')
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def send_report(args, log_file_name, token, api):
    kdir = args.kdir
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }
    data_map = {
        'job': 'tree',
        'kernel': 'kernel',
        'git_branch': 'branch',
        'arch': 'arch',
        'defconfig_full': 'defconfig',
        'build_environment': 'build_environment',
        'lab_name': 'lab',
        'device_type': 'target',
        'test_case_path': 'test_case',
        'good_commit': 'good',
        'bad_commit': 'bad',
        'subject': 'subject',
    }

    data = {k: getattr(args, v) for k, v in data_map.items()}
    to, cc = set(args.to.split(' ')), set()
    if all(check == 'PASS' for check in list(checks_dict(args).values())):
        add_git_recipients(kdir, 'refs/bisect/bad', to, cc)
    cc = cc.difference(to)

    print("Recipients:")
    for recipients, cat in (to, 'to'), (cc, 'cc'):
        print("{}:".format(cat))
        for r in recipients:
            print("  {}".format(r))

    if args.no_auto_recipients:
        print("Not sending to automatic recipients.  Final recipients:")
        to = set(args.to.split(' '))
        cc = set()
        for r in to:
            print("  {}".format(r))
    else:
        raise Exception("NOT SENDING PUBLIC EMAIL REPORTS FOR CHROMEOS YET")

    data.update({
        'report_type': 'bisect',
        'type': args.bisect_type,
        'log': log_file_name,
        'format': ['txt'],
        'send_to': list(to),
        'send_cc': list(cc),
        'delay': '60',
    })

    url = urllib.parse.urljoin(api, '/send')
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()


def main(args):
    # ToDo: get file_resource from build meta-data
    upload_path = '/'.join(getattr(args, k) for k in [
        'tree', 'branch', 'kernel', 'arch', 'defconfig',
        'build_environment', 'lab'])
    log_file_name = 'bisect-{}-{}.json'.format(args.test_case, args.target)

    print("Uploading bisect log: {}".format(upload_path))
    upload_log(args, upload_path, log_file_name, args.token, args.api)

    print("Sending bisection results")
    send_result(args, log_file_name, args.token, args.api)

    print("Sending bisection report email")
    send_report(args, log_file_name, args.token, args.api)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Push automated bisection results to the KernelCI backend API")
    parser.add_argument("--token",
                        help="KernelCI API Token", required=True)
    parser.add_argument("--api", required=True,
                        help="KernelCI API URL")
    parser.add_argument("--lab", required=True,
                        help="KernelCI lab name")
    parser.add_argument("--arch", required=True,
                        help="CPU architecture")
    parser.add_argument("--defconfig", required=True,
                        help="full defconfig")
    parser.add_argument("--build-environment", required=True,
                        help="build environment name")
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
    parser.add_argument("--bisect-type", default="test",
                        help="bisection type")
    parser.add_argument("--test-case", required=True,
                        help="test case path")
    parser.add_argument("--kdir", required=True,
                        help="path to the kernel directory")
    parser.add_argument("--subject", required=True,
                        help="email report subject")
    parser.add_argument("--to", required=True,
                        help="email recipients")
    parser.add_argument("--no-auto-recipients", action='store_true',
                        help="Disable automatic email recipients")
    args = parser.parse_args()
    main(args)
