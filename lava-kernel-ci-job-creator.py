#!/usr/bin/python
import urllib2
import urlparse
import re
import sys
import os
import shutil

base_url = None
kernel = None
dtb_list = []

arndale = {'device_type': 'arndale',
           'template': 'kernel-ci-template.json',
           'defconfig_blacklist': [],
           'lpae': True,
           'be': False}

arndale_octa = {'device_type': 'arndale-octa',
                'template': 'kernel-ci-template.json',
                'defconfig_blacklist': [],
                'lpae': True,
                'be': False}

beaglebone_black = {'device_type': 'beaglebone-black',
                    'template': 'kernel-ci-template.json',
                    'defconfig_blacklist': [],
                    'lpae': False,
                    'be': False}

beagle_xm = {'device_type': 'beagle-xm',
             'template': 'kernel-ci-template.json',
            'defconfig_blacklist': [],
             'lpae': False,
             'be': False}

panda_es = {'device_type': 'panda-es',
            'template': 'kernel-ci-template.json',
            'defconfig_blacklist': [],
            'lpae': False,
            'be': False}

cubieboard3 = {'device_type': 'cubieboard3',
               'template': 'kernel-ci-template.json',
               'defconfig_blacklist': [],
               'lpae': True,
               'be': False}

imx6q_wandboard = {'device_type': 'imx6q-wandboard',
                   'template': 'kernel-ci-template.json',
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig'],
                   'lpae': False,
                   'be': False}

dtb_map = {'exynos5250-arndale.dtb': arndale,
           'exynos5420-arndale-octa.dtb': arndale_octa,
           'am335x-boneblack.dtb': beaglebone_black,
           'omap3-beagle-xm.dtb': beagle_xm,
           'omap4-panda-es.dtb': panda_es,
           'sun7i-a20-cubietruck.dtb': cubieboard3,
           'imx6q-wandboard.dtb': imx6q_wandboard}

parse_re = re.compile('href="([^"]*)".*(..-...-.... ..:..).*?(\d+[^\s<]*|-)')

def setup_job_dir(directory):
    print 'Setting up JSON output directory at: jobs/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)
    print 'Done setting up JSON output directory'


def create_jobs(base_url, kernel, dtb_list):
    print 'Creating JSON Job Files...'
    cwd = os.getcwd()
    url = urlparse.urlparse(kernel)
    build_info = url.path.split('/')
    image_url = base_url
    image_type = build_info[1]
    tree = build_info[2]
    kernel_version = build_info[3]
    defconfig = build_info[4]

    for dtb in dtb_list:
        dtb_name = dtb.split('/')[-1]
        device = dtb_map[dtb_name]
        device_type = device['device_type']
        device_template = device['template']
        lpae = device['lpae']
        be = device['be']
        if 'BIG_ENDIAN' in defconfig and not be:
            print 'BIG_ENDIAN is not supported on %s. Skipping JSON creation' % device_type
        elif 'LPAE' in defconfig and not lpae:
            print 'LPAE is not supported on %s. Skipping JSON creation' % device_type
        elif defconfig in device['defconfig_blacklist']:
            print '%s has been blacklisted. Skipping JSON creation' % defconfig
        else:
            job_name = tree + '-' + kernel_version + '-' + defconfig + '-' + dtb_name
            job_json = cwd + '/jobs/' + job_name + '.json'
            template_file = cwd + '/templates/' + str(device_template)
            with open(job_json, 'wt') as fout:
                with open(template_file, "rt") as fin:
                    for line in fin:
                        tmp = line.replace('{dtb_url}', dtb)
                        tmp = tmp.replace('{kernel_url}', kernel)
                        #tmp = tmp.replace('{lava_server}', lava_server)
                        #tmp = tmp.replace('{bundle_stream}', bundle_stream)
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
    global dtb_list

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
        if name.endswith('zImage'):
            kernel = url + name
            base_url = url
        if name.endswith('.dtb') and name in dtb_map:
            dtb_list.append(url + name)

    for dir in dirs:
        if kernel is not None and base_url is not None and dtb_list:
            print 'Found boot artifacts at: %s' % base_url
            create_jobs(base_url, kernel, dtb_list)
            base_url = None
            kernel = None
            dtb_list = []
        walk_url(url + dir)


def main(url):
    setup_job_dir(os.getcwd() + '/jobs')
    print 'Scanning %s for boot information...' % url
    walk_url(url)
    print 'Done scanning for boot information'
    print 'Done creating JSON jobs'
    exit(0)

if __name__ == '__main__':
    main(sys.argv[1])