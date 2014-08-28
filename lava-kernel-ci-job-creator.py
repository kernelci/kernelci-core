#!/usr/bin/python
import urllib2
import urlparse
import re
import os
import shutil
import argparse

base_url = None
kernel = None
device_list = []

arndale = {'device_type': 'arndale',
           'templates': ['generic-arm-kernel-ci-boot-template.json'],
           'defconfig_blacklist': [],
           'lpae': True,
           'be': False}

arndale_octa = {'device_type': 'arndale-octa',
                'templates': ['generic-arm-kernel-ci-boot-template.json'],
                'defconfig_blacklist': [],
                'lpae': True,
                'be': False}

beaglebone_black = {'device_type': 'beaglebone-black',
                    'templates': ['generic-arm-kernel-ci-boot-template.json'],
                    'defconfig_blacklist': [],
                    'lpae': False,
                    'be': False}

beagle_xm = {'device_type': 'beagle-xm',
             'templates': ['generic-arm-kernel-ci-boot-template.json'],
             'defconfig_blacklist': [],
             'lpae': False,
             'be': False}

panda_es = {'device_type': 'panda-es',
            'templates': ['generic-arm-kernel-ci-boot-template.json'],
            'defconfig_blacklist': [],
            'lpae': False,
            'be': False}

cubieboard3 = {'device_type': 'cubieboard3',
               'templates': ['generic-arm-kernel-ci-boot-template.json'],
               'defconfig_blacklist': [],
               'lpae': True,
               'be': False}

imx6q_wandboard = {'device_type': 'imx6q-wandboard',
                   'templates': ['generic-arm-kernel-ci-boot-template.json'],
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig'],
                   'lpae': False,
                   'be': False}

qemu_aarch64 = {'device_type': 'qemu-aarch64',
                'templates': ['generic-arm64-kernel-ci-boot-template.json'],
                'defconfig_blacklist': ['arm64-allnoconfig',
                                        'arm64-allmodconfig'],
                'lpae': False,
                'be': False}

x86 = {'device_type': 'x86',
       'templates': ['generic-x86-kernel-ci-boot-template.json'],
       'defconfig_blacklist': ['x86-i386_defconfig',
                               'x86-allnoconfig',
                               'x86-allmodconfig'],
       'lpae': False,
       'be': False}

device_map = {'exynos5250-arndale.dtb': arndale,
           'exynos5420-arndale-octa.dtb': arndale_octa,
           'am335x-boneblack.dtb': beaglebone_black,
           'omap3-beagle-xm.dtb': beagle_xm,
           'omap4-panda-es.dtb': panda_es,
           'sun7i-a20-cubietruck.dtb': cubieboard3,
           'imx6q-wandboard.dtb': imx6q_wandboard,
           'arm64': qemu_aarch64,
           'x86': x86}

parse_re = re.compile('href="([^"]*)".*(..-...-.... ..:..).*?(\d+[^\s<]*|-)')

def setup_job_dir(directory):
    print 'Setting up JSON output directory at: jobs/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)
    print 'Done setting up JSON output directory'


def create_jobs(base_url, kernel, platform_list):
    print 'Creating JSON Job Files...'
    cwd = os.getcwd()
    url = urlparse.urlparse(kernel)
    build_info = url.path.split('/')
    image_url = base_url
    image_type = build_info[1]
    tree = build_info[2]
    kernel_version = build_info[3]
    defconfig = build_info[4]

    for platform in platform_list:
        platform_name = platform.split('/')[-1]
        device = device_map[platform_name]
        device_type = device['device_type']
        device_templates = device['templates']
        lpae = device['lpae']
        be = device['be']
        if 'BIG_ENDIAN' in defconfig and not be:
            print 'BIG_ENDIAN is not supported on %s. Skipping JSON creation' % device_type
        elif 'LPAE' in defconfig and not lpae:
            print 'LPAE is not supported on %s. Skipping JSON creation' % device_type
        elif defconfig in device['defconfig_blacklist']:
            print '%s has been blacklisted. Skipping JSON creation' % defconfig
        else:
            for template in device_templates:
                job_name = tree + '-' + kernel_version + '-' + defconfig + '-' + platform_name
                job_json = cwd + '/jobs/' + job_name + '.json'
                template_file = cwd + '/templates/' + str(template)
                with open(job_json, 'wt') as fout:
                    with open(template_file, "rt") as fin:
                        for line in fin:
                            tmp = line.replace('{dtb_url}', platform)
                            tmp = tmp.replace('{kernel_url}', kernel)
                            tmp = tmp.replace('{device_type}', device_type)
                            tmp = tmp.replace('{job_name}', job_name)
                            tmp = tmp.replace('{image_type}', image_type)
                            tmp = tmp.replace('{image_url}', image_url)
                            tmp = tmp.replace('{tree}', tree)
                            tmp = tmp.replace('{kernel_version}', kernel_version)
                            tmp = tmp.replace('{defconfig}', defconfig)
                            fout.write(tmp)
                print 'JSON Job created: jobs/%s' % job_name


def walk_url(url):
    global base_url
    global kernel
    global device_list

    try:
        html = urllib2.urlopen(url).read()
    except IOError, e:
        print 'error fetching %s: %s' % (url, e)
        exit(1)
    if not url.endswith('/'):
        url += '/'
    files = parse_re.findall(html)
    dirs = []
    for name, date, size in files:
        if name.endswith('/'):
            dirs += [name]
        if 'bzImage' in name and 'x86' in url:
            kernel = url + name
            base_url = url
            device_list.append(url + 'x86')
        if 'zImage' in name and 'arm' in url:
            kernel = url + name
            base_url = url
        if 'Image' in name and 'arm64' in url:
            kernel = url + name
            base_url = url
            device_list.append(url + 'arm64')
        if name.endswith('.dtb') and name in device_map:
            device_list.append(url + name)

    for dir in dirs:
        if kernel is not None and base_url is not None and device_list:
            print 'Found boot artifacts at: %s' % base_url
            create_jobs(base_url, kernel, device_list)
            base_url = None
            kernel = None
            device_list = []
        walk_url(url + dir)


def main(args):
    setup_job_dir(os.getcwd() + '/jobs')
    print 'Scanning %s for boot information...' % args.url
    walk_url(args.url)
    print 'Done scanning for boot information'
    print 'Done creating JSON jobs'
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="url to build artifacts")
    args = parser.parse_args()
    main(args)