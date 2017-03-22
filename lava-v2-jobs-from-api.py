#!/usr/bin/python
import urllib2
import urlparse
import httplib
import re
import os
import shutil
import argparse
import ConfigParser
import json
import sys
from lib.utils import setup_job_dir
from lib import configuration
from lib.device_map import device_map
from lib.utils import write_file
import requests
import urlparse
from jinja2 import Environment, FileSystemLoader


LEGACY_X86_PLATFORMS = ['x86', 'x86-kvm']
LEGACY_ARM64_PLATFORMS = ['qemu-aarch64-legacy']
INITRD_URLS = {'arm64': 'http://storage.kernelci.org/images/rootfs/buildroot/arm64/rootfs.cpio.gz',
               'arm64be': 'http://storage.kernelci.org/images/rootfs/buildroot/arm64be/rootfs.cpio.gz',
               'armeb': 'http://storage.kernelci.org/images/rootfs/buildroot/armeb/rootfs.cpio.gz',
               'armel': 'http://storage.kernelci.org/images/rootfs/buildroot/armel/rootfs.cpio.gz',
               'x86': 'http://storage.kernelci.org/images/rootfs/buildroot/x86/rootfs.cpio.gz'}


def main(args):
    config = configuration.get_config(args)
    plans = config.get("plans")
    targets = config.get("targets")
    if config.get("jobs"):
        job_dir = setup_job_dir(config.get("jobs"))
    else:
        job_dir = setup_job_dir(os.getcwd() + '/jobs')

    arch = args.get('arch')
    plans = args.get('plans')
    branch = args.get('branch')
    git_describe = args.get('describe')
    tree = args.get('tree')
    kernel = tree
    storage = args.get('storage')
    api = args.get('api')
    headers = {
        "Authorization": config.get('token')
    }

    print "Working on kernel %s/%s" % (tree, branch)
    url = urlparse.urljoin(api, ("/build?job=%s&kernel=%s&git_branch=%s&status=PASS&arch=%s" % (tree, git_describe, branch, arch)))
    print "Calling KernelCI API: %s" % url
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print "Error calling KernelCI API"
        print response
        print response.content
        sys.exit(1)
    data = json.loads(response.content)
    builds = data['result']
    print len(builds)
    jobs = []
    cwd = os.getcwd()
    for build in builds:
        defconfig = build['defconfig_full']
        arch_defconfig = ("%s-%s" % (arch, defconfig))
        print "Working on build %s" % arch_defconfig
        test_suite = None
        test_set = None
        test_desc = None
        test_type = None
        plan_defconfigs = []
        modules = build['modules']
        for plan in plans:
            if plan != 'boot':
                    config = ConfigParser.ConfigParser()
                    try:
                        config.read(cwd + '/templates/' + plan + '/' + plan + '.ini')
                        test_suite = config.get(plan, 'suite')
                        test_set = config.get(plan, 'set')
                        test_desc = config.get(plan, 'description')
                        test_type = config.get(plan, 'type')
                        plan_defconfigs = config.get(plan, 'defconfigs').split(',')
                    except:
                        print "Unable to load test configuration"
                        exit(1)
            if build['kernel_image']:
                # handle devices without a DTB, hacky :/
                if build['kernel_image'] == 'bzImage' and arch == 'x86':
                    build['dtb_dir_data'].extend(LEGACY_X86_PLATFORMS)
                if arch == 'arm64' and 'arm64-defconfig' in arch_defconfig:
                    build['dtb_dir_data'].extend(LEGACY_ARM64_PLATFORMS)
                for dtb in build['dtb_dir_data']:
                    # hack for arm64 dtbs in subfolders
                    dtb_full = dtb
                    if arch == 'arm64':
                        dtb = str(dtb).split('/')[-1]
                    if dtb in device_map:
                        # print "device %s was in the device_map" % dtb
                        for device in device_map[dtb]:
                            # print "working on device %s" % dtb
                            lpae = device['lpae']
                            device_type = device['device_type']
                            fastboot = str(device['fastboot']).lower()
                            blacklist = False
                            nfs_blacklist = False
                            if arch_defconfig in device['defconfig_blacklist']:
                                print "defconfig %s is blacklisted for device %s" % (defconfig, device['device_type'])
                                continue
                            elif "BIG_ENDIAN" in defconfig and plan != 'boot-be':
                                print "BIG_ENDIAN is not supported on %s" % device_type
                                continue
                            elif "LPAE" in defconfig and not lpae:
                                print "LPAE is not support on %s" % device_type
                                continue
                            elif any([x for x in device['kernel_blacklist'] if x in kernel]):
                                print "kernel %s is blacklisted for device %s" % (kernel, device_type)
                                continue
                            elif any([x for x in device['nfs_blacklist'] if x in kernel]) \
                                    and plan in ['boot-nfs', 'boot-nfs-mp']:
                                print "kernel %s is blacklisted for NFS on device %s" % (kernel, device_type)
                                continue
                            elif 'be_blacklist' in device \
                                    and any([x for x in device['be_blacklist'] if x in kernel]) \
                                    and plan in ['boot-be']:
                                print "kernel %s is blacklisted for BE on device %s" % (kernel, device_type)
                                continue
                            elif (arch_defconfig not in plan_defconfigs) and (plan != "boot"):
                                print "defconfig %s not in test plan %s" % (arch_defconfig, plan)
                                continue
                            elif targets is not None and device_type not in targets:
                                print "device_type %s is not in targets %s" % (device_type, targets)
                            else:
                                for template in device['templates']:
                                    short_template_file = plan + '/' + str(template)
                                    template_file = cwd + '/templates/' + short_template_file
                                    if os.path.exists(template_file) and template_file.endswith('.jinja2'):
                                        job_name = tree + '-' + branch + '-' + arch + "-" + defconfig[:100] + '-' + dtb + '-' + device_type + '-' + plan
                                        base_url = "%s/%s/%s/%s/%s/%s/" % (storage, build['job'], build['git_branch'], build['kernel'], arch_defconfig)
                                        dtb_url = base_url + "dtbs/" + dtb_full
                                        kernel_url = urlparse.urljoin(base_url, build['kernel_image'])
                                        defconfig_base = ''.join(defconfig.split('+')[:1])
                                        endian = 'little'
                                        if 'BIG_ENDIAN' in defconfig and plan == 'boot-be':
                                            endian = 'big'
                                        initrd_arch = arch
                                        if arch not in INITRD_URLS.keys():
                                            if arch == 'arm64' and endian == 'big':
                                                initrd_arch = 'arm64be'
                                            if arch == 'arm':
                                                if endian == 'big':
                                                    initrd_arch = 'armeb'
                                                else:
                                                    initrd_arch = 'armel'
                                        initrd_url = INITRD_URLS[initrd_arch]
                                        if build['modules']:
                                            modules_url = urlparse.urljoin(base_url, build['modules'])
                                        else:
                                            modules_url = None
                                        if device['device_type'].startswith('qemu') or device['device_type'] == 'kvm':
                                            device['device_type'] = 'qemu'
                                        job = {'name': job_name, 'dtb_url': dtb_url, 'platform': dtb_full, 'kernel_url': kernel_url, 'image_type': 'kernel-ci', 'image_url': base_url,
                                               'modules_url': modules_url, 'plan': plan, 'kernel': branch, 'tree': tree, 'defconfig': defconfig, 'fastboot': fastboot,
                                               'priority': args.get('priority'), 'device': device, 'template_file': template_file, 'base_url': base_url, 'endian': endian,
                                               'test_suite': test_suite, 'test_set': test_set, 'test_desc': test_desc, 'test_type': test_type, 'short_template_file': short_template_file,
                                               'arch': arch, 'arch_defconfig': arch_defconfig, 'git_branch': build['git_branch'], 'git_commit': build['git_commit'], 'git_describe': build['git_describe'],
                                               'defconfig_base': defconfig_base, 'initrd_url': initrd_url, 'kernel_image': build['kernel_image'], 'dtb_short': dtb}
                                        jobs.append(job)
            else:
                print "no kernel_image for %s" % build['defconfig_full']

    for job in jobs:
        job_file = job_dir + '/' + job['name'] + '.yaml'
        with open(job_file, 'w') as f:
            f.write(jinja_render(job))
        print "Job written: %s" % job_file


def jinja_render(job):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(job['short_template_file'])
    return template.render(job)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="KernelCI API Token")
    parser.add_argument("--api", help="KernelCI API URL", default="https://api.kernelci.org")
    parser.add_argument("--storage", help="KernelCI storage URL", default="https://storage.kernelci.org")
    parser.add_argument("--jobs", help="absolute path to top jobs folder")
    parser.add_argument("--tree", help="KernelCI build kernel tree")
    parser.add_argument("--branch", help="KernelCI build kernel branch")
    parser.add_argument("--describe", help="KernelCI build kernel git describe")
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default", help="section in the LAVA config file")
    parser.add_argument("--plans", nargs='+', required=True, help="test plan to create jobs for")
    parser.add_argument("--arch", help="specific architecture to create jobs for")
    parser.add_argument("--targets", nargs='+', help="specific targets to create jobs for")
    parser.add_argument("--priority", choices=['high', 'medium', 'low', 'HIGH', 'MEDIUM', 'LOW'],
                        help="priority for LAVA jobs", default='high')
    args = vars(parser.parse_args())
    main(args)
