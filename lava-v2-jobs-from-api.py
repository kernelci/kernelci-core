#!/usr/bin/python
#
# Copyright (C) 2016, 2017 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
#
# Copyright (C) 2017, 2018 Collabora Ltd
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
from jinja2 import Environment, FileSystemLoader
import json
import os
import requests
import time
import urllib
import urlparse

from lib import configuration, test_configs
from lib.utils import setup_job_dir


def get_builds(api, token, config):
    headers = {
        "Authorization": token,
    }
    url_params = {
        'job': config.get('tree'),
        'kernel': config.get('describe'),
        'git_branch': config.get('branch'),
        'arch': config.get('arch'),
    }
    job_defconfig = config.get('defconfig_full')
    if job_defconfig:
        url_params['defconfig_full'] = job_defconfig
        n_configs = 1
    else:
        n_configs = int(config.get('defconfigs'))
    url_params = urllib.urlencode(url_params)
    url = urlparse.urljoin(api, 'build?{}'.format(url_params))

    print("Calling KernelCI API: {}".format(url))

    builds = []
    loops = 10
    retry_time = 30
    for loop in range(loops):
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = json.loads(response.content)
        builds = data['result']
        if len(builds) >= n_configs:
            break
        print("Got fewer builds ({}) than expected ({}), retry in {} seconds"
              .format(len(builds), n_configs, retry_time))
        time.sleep(retry_time)

    return builds


def add_callback_params(params, config, plan):
    callback = config.get('callback')
    if not callback:
        return

    callback_type = config.get('callback_type')

    if callback_type == 'kernelci':
        lava_cb = 'boot' if plan == 'boot' else 'test'
        params['callback_name'] = '/'.join(['lava', lava_cb])

    params.update({
        'callback': callback,
        'callback_url': config.get('callback_url') or config.get('api'),
        'callback_dataset': config.get('callback_dataset'),
        'callback_type': callback_type,
    })


def get_job_params(config, test_config, defconfig, opts, build, plan):
    short_template_file = test_config.get_template_path(plan)
    template_file = os.path.join('templates', short_template_file)
    if not os.path.exists(template_file):
        print("Template not found: {}".format(template_file))
        return None

    arch = config.get('arch')
    storage = config.get('storage')
    device_type = test_config.device_type
    test_plan = test_config.test_plans[plan]
    defconfig_base = ''.join(defconfig.split('+')[:1])
    dtb = dtb_full = opts['dtb_full'] = opts['dtb'] = device_type.dtb

    # hack for arm64 dtbs in subfolders
    if arch == 'arm64' and dtb:
        dtb = opts['dtb'] = os.path.basename(dtb)

    file_server_resource = build.get('file_server_resource')
    if file_server_resource:
        job_name_prefix = file_server_resource.replace('/', '-')
        url_px = file_server_resource
    else:
        parts = [build['job'], build['git_branch'], build['kernel'], arch, defconfig]
        job_name_prefix = '-'.join(parts)
        url_px = '/'.join(parts)

    job_name = '-'.join([job_name_prefix, dtb or 'no-dtb', device_type.name, plan])

    base_url = urlparse.urljoin(storage, '/'.join([url_px, '']))
    kernel_url = urlparse.urljoin(
        storage, '/'.join([url_px, build['kernel_image']]))
    if dtb_full and dtb_full.endswith('.dtb'):
        dtb_url = urlparse.urljoin(
            storage, '/'.join([url_px, 'dtbs', dtb_full]))
        platform = opts['dtb'].split('.')[0]
    else:
        dtb_url = None
        platform = device_type.name
    if build['modules']:
        modules_url = urlparse.urljoin(
            storage, '/'.join([url_px, build['modules']]))
    else:
        modules_url = None

    rootfs = test_plan.rootfs

    job_params = {
        'name': job_name,
        'dtb_url': dtb_url,
        'dtb_short': dtb,
        'dtb_full': dtb_full,
        'platform': platform,
        'mach': device_type.mach,
        'kernel_url': kernel_url,
        'image_type': 'kernel-ci',
        'image_url': base_url,
        'modules_url': modules_url,
        'plan': plan,
        'kernel': config.get('describe'),
        'tree': config.get('tree'),
        'defconfig': defconfig,
        'arch_defconfig': opts['arch_defconfig'],
        'fastboot': str(device_type.get_flag('fastboot')).lower(),
        'priority': config.get('priority'),
        'device_type': device_type.name,
        'template_file': template_file,
        'base_url': base_url,
        'endian': opts['endian'],
        'short_template_file': short_template_file,
        'arch': arch,
        'git_branch': config.get('branch'),
        'git_commit': build['git_commit'],
        'git_describe': config.get('describe'),
        'git_url': build['git_url'],
        'defconfig_base': defconfig_base,
        'initrd_url': rootfs.get_url('ramdisk', arch, opts['endian']),
        'kernel_image': build['kernel_image'],
        'nfsrootfs_url': rootfs.get_url('nfs', arch, opts['endian']),
        'lab_name': config.get('lab'),
        'context': device_type.context,
        'rootfs_prompt': rootfs.prompt,
        'plan_name': test_plan.name,
        'file_server_resource': file_server_resource,
        'build_environment': build.get('build_environment'),
    }

    job_params.update(test_plan.params)
    add_callback_params(job_params, config, plan)

    return job_params


def add_jobs(jobs, config, tests, opts, build, plan, arch, defconfig):
    filters = {
        'arch': arch,
        'defconfig': defconfig,
        'kernel': config.get('describe'),
        'lab': config.get('lab'),
    }
    flags = {
        'big_endian': (opts['endian'] == 'big'),
        'lpae': 'LPAE' in defconfig,
    }
    dtbs = build['dtb_dir_data']
    targets = config.get('targets')

    for test_config in tests:
        if targets and str(test_config.device_type) not in targets:
            print("device not in targets: {}".format(
                test_config.device_type, targets))
            continue
        if not test_config.match(arch, plan, flags, filters):
            print("test config did not match: {}".format(
                test_config.device_type))
            continue
        dtb = test_config.device_type.dtb
        if dtb and dtb not in dtbs:
            print("dtb not in builds: {}".format(dtb))
            continue
        job_params = get_job_params(
            config, test_config, defconfig, opts, build, plan)
        if job_params:
            jobs.append(job_params)


def get_jobs_from_builds(config, builds, tests):
    arch = config.get('arch')
    cwd = os.getcwd()
    jobs = []

    for build in builds:
        if build.get('status') != 'PASS':
            continue

        defconfig = build['defconfig_full']
        print("Working on build: {}".format(build.get('file_server_resource')))

        for plan in config.get('plans'):
            opts = {
                'arch_defconfig': '-'.join([arch, defconfig]),
                'endian': 'big' if 'BIG_ENDIAN' in defconfig else 'little',
            }

            add_jobs(jobs, config, tests, opts, build, plan, arch, defconfig)

    return jobs


def write_jobs(config, jobs):
    job_dir = setup_job_dir(config.get('jobs') or config.get('lab'))
    for job in jobs:
        job_file = os.path.join(job_dir, '.'.join([job['name'], 'yaml']))
        with open(job_file, 'w') as f:
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template(job['short_template_file'])
            data = template.render(job)
            f.write(data)
        print("Job written: {}".format(job_file))


def main(args):
    config = configuration.get_config(args)
    token = config.get('token')
    api = config.get('api')
    storage = config.get('storage')
    builds_json = config.get('builds')

    print("Working on kernel {}/{}".format(
        config.get('tree'), config.get('branch')))

    if not storage:
        raise Exception("No KernelCI storage URL provided")

    if builds_json:
        print("Getting builds from {}".format(builds_json))
        with open(builds_json) as json_file:
            builds = json.load(json_file)
    else:
        print("Getting builds from KernelCI API")
        if not token:
            raise Exception("No KernelCI API token provided")
        if not api:
            raise Exception("No KernelCI API URL provided")
        builds = get_builds(api, token, config)

    print("Number of builds: {}".format(len(builds)))

    config_data = test_configs.load_from_yaml(config.get('test_configs'))
    tests = config_data['test_configs']
    print("Number of test configs: {}".format(len(tests)))

    jobs = get_jobs_from_builds(config, builds, tests)
    print("Number of jobs: {}".format(len(jobs)))

    write_jobs(config, jobs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",
                        help="path to KernelCI configuration file")
    parser.add_argument("--test-configs", default="test-configs.yaml",
                        help="path to KernelCI configuration file")
    parser.add_argument("--token",
                        help="KernelCI API Token")
    parser.add_argument("--api",
                        help="KernelCI API URL")
    parser.add_argument("--storage",
                        help="KernelCI storage URL")
    parser.add_argument("--builds",
                        help="Path to a JSON file to use rather than the API")
    parser.add_argument("--lab", required=True,
                        help="KernelCI Lab Name")
    parser.add_argument("--jobs",
                        help="absolute path to top jobs folder")
    parser.add_argument("--tree", required=True,
                        help="KernelCI build kernel tree")
    parser.add_argument("--branch", required=True,
                        help="KernelCI build kernel branch")
    parser.add_argument("--describe", required=True,
                        help="KernelCI build kernel git describe")
    parser.add_argument("--section", default="default",
                        help="section in the KernelCI config file")
    parser.add_argument("--plans", nargs='+', required=True,
                        help="test plan to create jobs for")
    parser.add_argument("--arch", required=True,
                        help="specific architecture to create jobs for")
    parser.add_argument("--targets", nargs='+',
                        help="specific targets to create jobs for")
    parser.add_argument("--priority", choices=['high', 'medium', 'low'],
                        help="priority for LAVA jobs", default='high')
    parser.add_argument("--callback",
                        help="add a callback with the given token name")
    parser.add_argument("--callback-url",
                        help="alternative URL to use instead of the API")
    parser.add_argument("--callback-type", choices=['kernelci', 'custom'],
                        default='kernelci',
                        help="type of arguments to append to the URL")
    parser.add_argument("--callback-dataset", default='all',
                        choices=['minimal', 'logs', 'results', 'all'],
                        help="type of dataset to receive in callback")
    parser.add_argument("--defconfigs", default=0,
                        help="Expected number of defconfigs from the API")
    parser.add_argument("--defconfig_full",
                        help="Only look for builds from this full defconfig")
    args = vars(parser.parse_args())
    if args:
        main(args)
    else:
        exit(1)
