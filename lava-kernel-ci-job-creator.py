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
dtb_map = {'exynos5250-arndale.dtb': 'arndale',
           'am335x-boneblack.dtb': 'beaglebone-black',
           'omap3-beagle-xm.dtb': 'beagle-xm',
           'omap4-panda-es.dtb': 'panda',
           'imx6dl-wandboard.dtb': 'imx6q-wandboard',
           'imx6q-wandboard.dtb': 'imx6q-wandboard'}

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
        job_name = tree + '-' + kernel_version + '-' + defconfig + '-' + dtb.split('/')[-1]
        job_json = cwd + '/jobs/' + job_name + '.json'
        template_file = cwd + '/templates/kernel-ci-template.json'
        with open(job_json, 'wt') as fout:
            with open(template_file, "rt") as fin:
                for line in fin:
                    tmp = line.replace('{dtb_url}', dtb)
                    tmp = tmp.replace('{kernel_url}', kernel)
                    #tmp = tmp.replace('{lava_server}', lava_server)
                    #tmp = tmp.replace('{bundle_stream}', bundle_stream)
                    #tmp = tmp.replace('{device_type}', device_type)
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