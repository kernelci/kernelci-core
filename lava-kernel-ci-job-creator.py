#!/usr/bin/python
#
# Copyright (C) 2014, 2015, 2016, 2017 Linaro Limited
# Author: Anders Roxell <anders.roxell@linaro.org>
# Author: Chase Qi <chase.qi@linaro.org>
# Author: Matt Hart <matthew.hart@linaro.org>
# Author: Milo Casagrande <milo.casagrande@linaro.org>
# Author: Tyler Baker <Tyler Baker tyler.baker@linaro.org>
#
# Copyright (C) 2016 Baylibre SAS
# Author: Kevin Hilman <khilman@baylibre.com>
# Author: Marc Titinger <mtitinger@baylibre.com>
#
# Copyright (C) 2016 Collabora Limited
# Author: Sjoerd Simons <sjoerd.simons@collabora.co.uk>
#
# Copyright (C) 2016 Pengutronix
# Author: Jan Luebbe <jlu@pengutronix.de>
#
# Copyright (C) 2016 Free Electrons
# Author: Quentin Schulz <quentin.schulz@free-electrons.com>
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

import urllib2
import urlparse
import httplib
import re
import os
import shutil
import argparse
import ConfigParser

from lib import configuration, device_map
from lib.utils import setup_job_dir

base_url = None
kernel = None
platform_list = []
legacy_platform_list = []
directory = None

parse_re = re.compile('href="([^./"?][^"?]*)"')



def create_jobs(base_url, kernel, plans, platform_list, targets, priority):
    global directory
    print 'Creating JSON Job Files...'
    cwd = os.getcwd()
    url = urlparse.urlparse(kernel)
    build_info = url.path.split('/')
    image_url = base_url
    # TODO: define image_type dynamically
    image_type = 'kernel-ci'
    tree = build_info[1]
    branch = build_info[2]
    kernel_version = build_info[3]
    arch = build_info[4]
    defconfig = build_info[5]
    arch_defconfig = ("%s-%s" % (arch, defconfig))
    has_modules = True
    checked_modules = False

    for platform in platform_list:
        platform_name = platform.split('/')[-1]
        for device in device_map[platform_name]:
            device_type = device['device_type']
            device_templates = device['templates']
            lpae = device['lpae']
            fastboot = device['fastboot']
            test_suite = None
            test_set = None
            test_desc = None
            test_type = None
            defconfigs = []
            for plan in plans:
                if plan != 'boot':
                        config = ConfigParser.ConfigParser()
                        try:
                            config.read(cwd + '/templates/' + plan + '/' + plan + '.ini')
                            test_suite = config.get(plan, 'suite')
                            test_set = config.get(plan, 'set')
                            test_desc = config.get(plan, 'description')
                            test_type = config.get(plan, 'type')
                            defconfigs = config.get(plan, 'defconfigs').split(',')
                        except:
                            print "Unable to load test configuration"
                            exit(1)
                if 'BIG_ENDIAN' in defconfig and plan != 'boot-be':
                    print 'BIG_ENDIAN is not supported on %s. Skipping JSON creation' % device_type
                elif 'LPAE' in defconfig and not lpae:
                    print 'LPAE is not supported on %s. Skipping JSON creation' % device_type
                elif any([x for x in device['kernel_defconfig_blacklist'] if x['kernel_version'] in kernel_version
                          and x['defconfig'] in defconfig]):
                    print '%s %s has been blacklisted. Skipping JSON creation' % (kernel_version, defconfig)
                elif defconfig in device['defconfig_blacklist']:
                    print '%s has been blacklisted. Skipping JSON creation' % defconfig
                elif any([x for x in device['kernel_blacklist'] if x in kernel_version]):
                    print '%s has been blacklisted. Skipping JSON creation' % kernel_version
                elif any([x for x in device['nfs_blacklist'] if x in kernel_version]) \
                        and plan in ['boot-nfs', 'boot-nfs-mp']:
                    print '%s has been blacklisted. Skipping JSON creation' % kernel_version
                elif 'be_blacklist' in device \
                        and any([x for x in device['be_blacklist'] if x in kernel_version]) \
                        and plan in ['boot-be']:
                    print '%s has been blacklisted. Skipping JSON creation' % kernel_version
                elif targets is not None and device_type not in targets:
                    print '%s device type has been omitted. Skipping JSON creation.' % device_type
                elif not any([x for x in defconfigs if x == arch_defconfig]) and plan != 'boot':
                    print '%s has been omitted from the %s test plan. Skipping JSON creation.' % (defconfig, plan)
                elif 'kselftest' in defconfig and plan != 'kselftest':
                    print "Skipping kselftest defconfig because plan was not kselftest"
                else:
                    for template in device_templates:
                        job_name = tree + '-' + branch + '-' + kernel_version + '-' + arch + '-' + defconfig[:100] + '-' + platform_name + '-' + device_type + '-' + plan
                        job_json = directory + '/' + job_name + '.json'
                        template_file = cwd + '/templates/' + plan + '/' + str(template)
                        if os.path.exists(template_file) and template_file.endswith('.json'):
                            with open(job_json, 'wt') as fout:
                                with open(template_file, "rt") as fin:
                                    for line in fin:
                                        tmp = line.replace('{dtb_url}', platform)
                                        tmp = tmp.replace('{kernel_url}', kernel)
                                        tmp = tmp.replace('{device_type}', device_type)
                                        tmp = tmp.replace('{job_name}', job_name)
                                        tmp = tmp.replace('{image_type}', image_type)
                                        tmp = tmp.replace('{image_url}', image_url)
                                        modules_url = image_url + 'modules.tar.xz'
                                        dummy_modules_url = 'https://storage.kernelci.org/modules/modules.tar.xz'
                                        if has_modules:
                                            # Check if the if the modules actually exist
                                            if not checked_modules:
                                                # We only need to check that the modules
                                                # exist once for each defconfig
                                                p = urlparse.urlparse(modules_url)
                                                if modules_url.startswith('https'):
                                                    conn = httplib.HTTPSConnection(p.netloc)
                                                else:
                                                    conn = httplib.HTTPConnection(p.netloc)
                                                conn.request('HEAD', p.path)
                                                resp = conn.getresponse()
                                                if resp.status > 400:
                                                    has_modules = False
                                                    print "No modules found, using dummy modules"
                                                    modules_url = dummy_modules_url
                                                checked_modules = True
                                        else:
                                            modules_url = dummy_modules_url
                                        tmp = tmp.replace('{modules_url}', modules_url)
                                        tmp = tmp.replace('{tree}', tree)
                                        if platform_name.endswith('.dtb'):
                                            tmp = tmp.replace('{device_tree}', platform_name)
                                        tmp = tmp.replace('{kernel_describe}', kernel_version)
                                        if 'BIG_ENDIAN' in defconfig and plan == 'boot-be':
                                            tmp = tmp.replace('{endian}', 'big')
                                        else:
                                            tmp = tmp.replace('{endian}', 'little')
                                        tmp = tmp.replace('{defconfig}', defconfig)
                                        tmp = tmp.replace('{fastboot}', str(fastboot).lower())
                                        if plan:
                                            tmp = tmp.replace('{test_plan}', plan)
                                        if test_suite:
                                            tmp = tmp.replace('{test_suite}', test_suite)
                                        if test_set:
                                            tmp = tmp.replace('{test_set}', test_set)
                                        if test_desc:
                                            tmp = tmp.replace('{test_desc}', test_desc)
                                        if test_type:
                                            tmp = tmp.replace('{test_type}', test_type)
                                        if priority:
                                            tmp = tmp.replace('{priority}', priority.lower())
                                        else:
                                            tmp = tmp.replace('{priority}', 'high')
                                        tmp = tmp.replace('{kernel_tree}', tree)
                                        tmp = tmp.replace('{kernel_branch}', branch)
                                        tmp = tmp.replace('{arch}', arch)
                                        fout.write(tmp)
                            print 'JSON Job created: jobs/%s' % job_name


def walk_url(url, plans=None, arch=None, targets=None, priority=None):
    global base_url
    global kernel
    global platform_list
    global legacy_platform_list

    if not url.endswith('/'):
        url += '/'

    try:
        html = urllib2.urlopen(url, timeout=30).read()
    except IOError, e:
        print 'error fetching %s: %s' % (url, e)
        exit(1)

    files = parse_re.findall(html)
    dirs = []
    for name in files:
        if name.endswith('/'):
            dirs += [name]
        if arch is None:
            if 'bzImage' in name and 'x86' in url:
                kernel = url + name
                base_url = url
                platform_list.append(url + 'x86')
                platform_list.append(url + 'x86-kvm')
                platform_list.append(url + 'qemu-i386')
            if 'zImage' in name and 'arm' in url:
                kernel = url + name
                base_url = url
            if 'Image' in name and 'arm64' in url:
                kernel = url + name
                base_url = url
                # qemu-aarch64,legacy
                if 'arm64/defconfig' in url:
                    legacy_platform_list.append(url + 'qemu-aarch64-legacy')
            if name.endswith('.dtb') and name in device_map:
                if base_url and base_url in url:
                    platform_list.append(url + name)
        elif arch == 'x86':
            if 'bzImage' in name and 'x86' in url:
                kernel = url + name
                base_url = url
                platform_list.append(url + 'x86')
                platform_list.append(url + 'x86-kvm')
                platform_list.append(url + 'qemu-i386')
        elif arch == 'arm':
            if 'zImage' in name and 'arm' in url:
                kernel = url + name
                base_url = url
            if name.endswith('.dtb') and name in device_map:
                if base_url and base_url in url:
                    legacy_platform_list.append(url + name)
        elif arch == 'arm64':
            if 'Image' in name and 'arm64' in url:
                kernel = url + name
                base_url = url
                # qemu-aarch64,legacy
                if 'arm64/defconfig' in url:
                    legacy_platform_list.append(url + 'qemu-aarch64-legacy')
            if name.endswith('.dtb') and name in device_map:
                if base_url and base_url in url:
                    platform_list.append(url + name)

    if kernel is not None and base_url is not None:
        if platform_list:
            print 'Found artifacts at: %s' % base_url
            create_jobs(base_url, kernel, plans, platform_list, targets,
                        priority)
            # Hack for subdirectories with arm64 dtbs
            if 'arm64' not in base_url:
                base_url = None
                kernel = None
            platform_list = []
        elif legacy_platform_list:
            print 'Found artifacts at: %s' % base_url
            create_jobs(base_url, kernel, plans, legacy_platform_list, targets,
                        priority)
            legacy_platform_list = []

    for dir in dirs:
        walk_url(url + dir, plans, arch, targets, priority)

def main(args):
    global directory
    config = configuration.get_config(args)
    if config.get("jobs"):
        directory = setup_job_dir(config.get("jobs"))
    else:
        directory = setup_job_dir(os.getcwd() + '/jobs')
    url = config.get('url')
    arch = config.get('arch')
    if arch:
        url += arch + "/"
    print 'Scanning %s for kernel information...' % config.get("url")
    walk_url(url, config.get("plans"), arch, config.get("targets"), config.get("priority"))
    print 'Done scanning for kernel information'
    print 'Done creating JSON jobs'
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="url to build artifacts")
    parser.add_argument("--jobs", help="absolute path to top jobs folder")
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default", help="section in the LAVA config file")
    parser.add_argument("--plans", nargs='+', required=True, help="test plan to create jobs for")
    parser.add_argument("--arch", help="specific architecture to create jobs for")
    parser.add_argument("--targets", nargs='+', help="specific targets to create jobs for")
    parser.add_argument("--priority", choices=['high', 'medium', 'low', 'HIGH', 'MEDIUM', 'LOW'],
                        help="priority for LAVA jobs")
    args = vars(parser.parse_args())
    main(args)
