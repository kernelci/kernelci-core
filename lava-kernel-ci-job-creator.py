#!/usr/bin/python
import urllib2
import urlparse
import re
import os
import shutil
import argparse

base_url = None
kernel = None
platform_list = []
legacy_platform_list = []

arndale = {'device_type': 'arndale',
           'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
           'defconfig_blacklist': [],
           'lpae': True,
           'be': False,
           'fastboot': False}

snow = {'device_type': 'snow',
        'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
        'defconfig_blacklist': [],
        'lpae': True,
        'be': False,
        'fastboot': False}

arndale_octa = {'device_type': 'arndale-octa',
                'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
                'defconfig_blacklist': [],
                'lpae': True,
                'be': False,
                'fastboot': False}

peach_pi = {'device_type': 'peach-pi',
            'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
            'defconfig_blacklist': [],
            'lpae': True,
            'be': False,
            'fastboot': False}

odroid_xu3 = {'device_type': 'odroid-xu3',
              'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
              'defconfig_blacklist': [],
              'lpae': True,
              'be': False,
              'fastboot': False}

odroid_u2 = {'device_type': 'odroid-u2',
             'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
             'defconfig_blacklist': [],
             'lpae': False,
             'be': False,
             'fastboot': False}

odroid_x2 = {'device_type': 'odroid-x2',
             'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
             'defconfig_blacklist': [],
             'lpae': False,
             'be': False,
             'fastboot': False}

beaglebone_black = {'device_type': 'beaglebone-black',
                    'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
                    'defconfig_blacklist': [],
                    'lpae': False,
                    'be': False,
                    'fastboot': False}

beagle_xm = {'device_type': 'beagle-xm',
             'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
             'defconfig_blacklist': [],
             'lpae': False,
             'be': False,
             'fastboot': False}

beagle_xm_legacy = {'device_type': 'beagle-xm',
                    'templates': ['generic-arm-uboot-kernel-ci-boot-template.json'],
                    'defconfig_blacklist': [],
                    'lpae': False,
                    'be': False,
                    'fastboot': False}

panda_es = {'device_type': 'panda-es',
            'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
            'defconfig_blacklist': [],
            'lpae': False,
            'be': False,
            'fastboot': False}

panda = {'device_type': 'panda',
         'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
         'defconfig_blacklist': [],
         'lpae': False,
         'be': False,
         'fastboot': False}

cubieboard3 = {'device_type': 'cubieboard3',
               'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
               'defconfig_blacklist': [],
               'lpae': True,
               'be': False,
               'fastboot': False}

hisi_x5hd2_dkb = {'device_type': 'hi3716cv200',
                  'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
                  'defconfig_blacklist': [],
                  'lpae': False,
                  'be': False,
                  'fastboot': False}

d01 = {'device_type': 'd01',
       'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
       'defconfig_blacklist': [],
       'lpae': True,
       'be': False,
       'fastboot': False}

imx6q_wandboard = {'device_type': 'imx6q-wandboard',
                   'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig'],
                   'lpae': False,
                   'be': False,
                   'fastboot': False}

imx6q_sabrelite = {'device_type': 'imx6q-sabrelite',
                   'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig'],
                   'lpae': False,
                   'be': False,
                   'fastboot': False}

utilite_pro = {'device_type': 'utilite-pro',
               'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
               'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                       'arm-multi_v5_defconfig'],
               'lpae': False,
               'be': False,
               'fastboot': False}

snowball = {'device_type': 'snowball',
            'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
            'defconfig_blacklist': [],
            'lpae': False,
            'be': False,
            'fastboot': False}

ifc6540 = {'device_type': 'ifc6540',
           'templates': ['generic-arm-ifc6540-kernel-ci-boot-template.json'],
           'defconfig_blacklist': [],
           'lpae': False,
           'be': False,
           'fastboot': True}

ifc6410 = {'device_type': 'ifc6410',
           'templates': ['generic-arm-ifc6410-kernel-ci-boot-template.json'],
           'defconfig_blacklist': [],
           'lpae': False,
           'be': False,
           'fastboot': True}

sama53d = {'device_type': 'sama53d',
           'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
           'defconfig_blacklist': ['arm-at91_dt_defconfig',
                                   'arm-at91sam9260_9g20_defconfig',
                                   'arm-at91sam9g45_defconfig'],
           'lpae': False,
           'be': False,
           'fastboot': False}

jetson_tk1 = {'device_type': 'jetson-tk1',
              'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
              'defconfig_blacklist': [],
              'lpae': True,
              'be': False,
              'fastboot': False}

parallella = {'device_type': 'parallella',
              'templates': ['generic-arm-uboot-dtb-kernel-ci-boot-template.json'],
              'defconfig_blacklist': [],
              'lpae': False,
              'be': False,
              'fastboot': False}

optimus_a80 = {'device_type': 'optimus-a80',
              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
              'defconfig_blacklist': [],
              'lpae': True,
              'be': False,
              'fastboot': True}

cubieboard4 = {'device_type': 'cubieboard4',
              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
              'defconfig_blacklist': [],
              'lpae': True,
              'be': False,
              'fastboot': True}

qemu_arm_cortex_a9 = {'device_type': 'qemu-arm-cortex-a9',
                      'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
                      'defconfig_blacklist': [],
                      'lpae': False,
                      'be': False,
                      'fastboot': False}

qemu_arm_cortex_a9_legacy = {'device_type': 'qemu-arm-cortex-a9',
                             'templates': ['generic-arm-kernel-ci-boot-template.json'],
                             'defconfig_blacklist': [],
                             'lpae': False,
                             'be': False,
                             'fastboot': False}

qemu_arm_cortex_a15_a7 = {'device_type': 'qemu-arm-cortex-a15',
                          'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
                          'defconfig_blacklist': [],
                          'lpae': True,
                          'be': False,
                          'fastboot': False}

qemu_arm_cortex_a15 = {'device_type': 'qemu-arm-cortex-a15',
                       'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
                       'defconfig_blacklist': [],
                       'lpae': True,
                       'be': False,
                       'fastboot': False}

qemu_arm_cortex_a15_legacy = {'device_type': 'qemu-arm-cortex-a15',
                              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
                              'defconfig_blacklist': [],
                              'lpae': True,
                              'be': False,
                              'fastboot': False}

qemu_arm = {'device_type': 'qemu-arm',
            'templates': ['generic-arm-kernel-ci-boot-template.json'],
            'defconfig_blacklist': [],
            'lpae': False,
            'be': False,
            'fastboot': False}

qemu_aarch64 = {'device_type': 'qemu-aarch64',
                'templates': ['generic-arm64-kernel-ci-boot-template.json'],
                'defconfig_blacklist': ['arm64-allnoconfig',
                                        'arm64-allmodconfig'],
                'lpae': False,
                'be': False,
                'fastboot': False}

apm_mustang = {'device_type': 'mustang',
               'templates': ['generic-arm64-uboot-dtb-kernel-ci-boot-template.json'],
               'defconfig_blacklist': ['arm64-allnoconfig',
                                       'arm64-allmodconfig'],
               'lpae': False,
               'be': False,
               'fastboot': False}

juno = {'device_type': 'juno',
        'templates': ['juno-arm64-dtb-kernel-ci-boot-template.json'],
        'defconfig_blacklist': ['arm64-allnoconfig',
                                'arm64-allmodconfig'],
        'lpae': False,
        'be': False,
        'fastboot': False}


x86 = {'device_type': 'x86',
       'templates': ['generic-x86-kernel-ci-boot-template.json'],
       'defconfig_blacklist': ['x86-i386_defconfig',
                               'x86-allnoconfig',
                               'x86-allmodconfig',
                               'x86-tiny.config',
                               'x86-kvm_guest.config'],
       'lpae': False,
       'be': False,
       'fastboot': False}

minnowboard_max_E3825 = {'device_type': 'minnowboard-max-E3825',
                         'templates': ['generic-x86-kernel-ci-boot-template.json'],
                         'defconfig_blacklist': ['x86-i386_defconfig',
                                                 'x86-allnoconfig',
                                                 'x86-allmodconfig',
                                                 'x86-tiny.config',
                                                 'x86-kvm_guest.config'],
                        'lpae': False,
                        'be': False,
                        'fastboot': False}

x86_kvm = {'device_type': 'kvm',
           'templates': ['generic-x86-kernel-ci-boot-template.json'],
           'defconfig_blacklist': ['x86-i386_defconfig',
                                   'x86-allnoconfig',
                                   'x86-allmodconfig',
                                   'x86-tiny.config',
                                   'x86-kvm_guest.config'],
           'lpae': False,
           'be': False,
           'fastboot': False}

device_map = {'exynos5250-arndale.dtb': [arndale],
              'exynos5250-snow.dtb': [snow],
              'exynos5420-arndale-octa.dtb': [arndale_octa],
              'exynos5800-peach-pi.dtb': [peach_pi],
              'exynos5422-odroidxu3.dtb': [odroid_xu3],
              'exynos4412-odroidu3.dtb': [odroid_u2],
              'exynos4412-odroidx2.dtb': [odroid_x2],
              'am335x-boneblack.dtb': [beaglebone_black],
              'omap3-beagle-xm.dtb': [beagle_xm],
              'omap3-beagle-xm-legacy': [beagle_xm_legacy],
              'omap4-panda-es.dtb': [panda_es],
              'omap4-panda.dtb': [panda],
              'sun7i-a20-cubietruck.dtb': [cubieboard3],
              'hip04-d01.dtb': [d01],
              'hisi-x5hd2-dkb.dtb': [hisi_x5hd2_dkb],
              'imx6q-wandboard.dtb': [imx6q_wandboard],
              'imx6q-sabrelite.dtb': [imx6q_sabrelite],
              'imx6q-cm-fx6.dtb': [utilite_pro],
              'ste-snowball.dtb': [snowball],
              'qcom-apq8084-ifc6540.dtb': [ifc6540],
              'qcom-apq8064-ifc6410.dtb': [ifc6410],
              'at91-sama5d3_xplained.dtb': [sama53d],
              'tegra124-jetson-tk1.dtb': [jetson_tk1],
              'zynq-parallella.dtb': [parallella],
              'sun9i-a80-optimus.dtb': [optimus_a80, cubieboard4],
              'vexpress-v2p-ca15-tc1.dtb': [qemu_arm_cortex_a15],
              'vexpress-v2p-ca15-tc1-legacy': [qemu_arm_cortex_a15_legacy],
              'vexpress-v2p-ca15_a7.dtb': [qemu_arm_cortex_a15_a7],
              'vexpress-v2p-ca9.dtb': [qemu_arm_cortex_a9],
              'vexpress-v2p-ca9-legacy': [qemu_arm_cortex_a9_legacy],
              'qemu-arm-legacy': [qemu_arm],
              'qemu-aarch64-legacy': [qemu_aarch64],
              'apm-mustang.dtb': [apm_mustang],
              'juno.dtb': [juno],
              'x86': [x86, minnowboard_max_E3825],
              'x86-kvm': [x86_kvm]}

parse_re = re.compile('href="([^./"?][^"?]*)"')

def setup_job_dir(directory):
    print 'Setting up JSON output directory at: jobs/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        shutil.rmtree(directory)
        os.makedirs(directory)
    print 'Done setting up JSON output directory'


def create_jobs(base_url, kernel, platform_list, target, targets):
    print 'Creating JSON Job Files...'
    cwd = os.getcwd()
    url = urlparse.urlparse(kernel)
    build_info = url.path.split('/')
    image_url = base_url
    # TODO: define image_type dynamically
    image_type = 'kernel-ci'
    tree = build_info[1]
    kernel_version = build_info[2]
    defconfig = build_info[3]

    for platform in platform_list:
        platform_name = platform.split('/')[-1]
        for device in device_map[platform_name]:
            device_type = device['device_type']
            device_templates = device['templates']
            lpae = device['lpae']
            be = device['be']
            fastboot = device['fastboot']
            if 'BIG_ENDIAN' in defconfig and not be:
                print 'BIG_ENDIAN is not supported on %s. Skipping JSON creation' % device_type
            elif 'LPAE' in defconfig and not lpae:
                print 'LPAE is not supported on %s. Skipping JSON creation' % device_type
            elif defconfig in device['defconfig_blacklist']:
                print '%s has been blacklisted. Skipping JSON creation' % defconfig
            elif target is not None and target != device_type:
                print '%s device type has been omitted. Skipping JSON creation.' % device_type
            elif targets is not None and device_type not in targets:
                print '%s device type has been omitted. Skipping JSON creation.' % device_type
            else:
                for template in device_templates:
                    job_name = tree + '-' + kernel_version + '-' + defconfig[:100] + '-' + platform_name + '-' + device_type
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
                                if platform_name.endswith('.dtb'):
                                    tmp = tmp.replace('{device_tree}', platform_name)
                                tmp = tmp.replace('{kernel_version}', kernel_version)
                                if 'BIG_ENDIAN' in defconfig and be:
                                    tmp = tmp.replace('{endian}', 'big')
                                else:
                                    tmp = tmp.replace('{endian}', 'little')
                                tmp = tmp.replace('{defconfig}', defconfig)
                                tmp = tmp.replace('{fastboot}', str(fastboot).lower())
                                fout.write(tmp)
                    print 'JSON Job created: jobs/%s' % job_name


def walk_url(url, arch=None, target=None, targets=None):
    global base_url
    global kernel
    global platform_list
    global legacy_platform_list

    try:
        html = urllib2.urlopen(url).read()
    except IOError, e:
        print 'error fetching %s: %s' % (url, e)
        exit(1)
    if not url.endswith('/'):
        url += '/'
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
            if 'zImage' in name and 'arm' in url:
                kernel = url + name
                base_url = url
                # qemu-arm,legacy
                if 'arm-versatile_defconfig' in url:
                    legacy_platform_list.append(url + 'qemu-arm-legacy')
                # omap3-beagle-xm,legacy
                if 'arm-omap2plus_defconfig' in base_url:
                    legacy_platform_list.append(url + 'omap3-beagle-xm-legacy')
            if 'Image' in name and 'arm64' in url:
                kernel = url + name
                base_url = url
                # qemu-aarch64,legacy
                if 'arm64-defconfig' in url:
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
        elif arch == 'arm':
            if 'zImage' in name and 'arm' in url:
                kernel = url + name
                base_url = url
                # qemu-arm,legacy
                if 'arm-versatile_defconfig' in url:
                    legacy_platform_list.append(url + 'qemu-arm-legacy')
                # omap3-beagle-xm,legacy
                if 'arm-omap2plus_defconfig' in base_url:
                    legacy_platform_list.append(url + 'omap3-beagle-xm-legacy')
            if name.endswith('.dtb') and name in device_map:
                if base_url and base_url in url:
                    legacy_platform_list.append(url + name)
        elif arch == 'arm64':
            if 'Image' in name and 'arm64' in url:
                kernel = url + name
                base_url = url
                # qemu-aarch64,legacy
                if 'arm64-defconfig' in url:
                    legacy_platform_list.append(url + 'qemu-aarch64-legacy')
            if name.endswith('.dtb') and name in device_map:
                if base_url and base_url in url:
                    platform_list.append(url + name)

    if kernel is not None and base_url is not None:
        if platform_list:
            print 'Found boot artifacts at: %s' % base_url
            create_jobs(base_url, kernel, platform_list, target, targets)
            # Hack for subdirectories with arm64 dtbs
            if 'arm64' not in base_url:
                base_url = None
                kernel = None
            platform_list = []
        elif legacy_platform_list:
            print 'Found boot artifacts at: %s' % base_url
            create_jobs(base_url, kernel, legacy_platform_list, target, targets)
            legacy_platform_list = []

    for dir in dirs:
        walk_url(url + dir, arch, target, targets)


def main(args):
    setup_job_dir(os.getcwd() + '/jobs')
    print 'Scanning %s for boot information...' % args.url
    walk_url(args.url, args.arch, args.target, args.targets)
    print 'Done scanning for boot information'
    print 'Done creating JSON jobs'
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="url to build artifacts")
    parser.add_argument("--arch", help="specific architecture to create jobs for")
    parser.add_argument("--target", help="specific target to create jobs for")
    parser.add_argument("--targets", nargs='+', help="specific targets to create jobs for")
    args = parser.parse_args()
    main(args)