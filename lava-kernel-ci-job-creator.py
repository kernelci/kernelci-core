#!/usr/bin/python
import urllib2
import urlparse
import re
import os
import shutil
import argparse
import ConfigParser

base_url = None
kernel = None
platform_list = []
legacy_platform_list = []
no_modules_list = ['arm-sunxi_defconfig',
                   'arm-hisi_defconfig',
                   'arm-bcm2835_defconfig']

bcm2835_rpi_b_plus = {'device_type': 'bcm2835-rpi-b-plus',
                      'templates': ['generic-arm-dtb-kernel-ci-boot-template.json'],
                      'defconfig_blacklist': ['arm-allmodconfig'],
                      'kernel_blacklist': [],
                      'lpae': False,
                      'fastboot': False}

armada_370_mirabox = {'device_type': 'armada-370-mirabox',
                       'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                     'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                       'defconfig_blacklist': ['arm-allmodconfig'],
                       'kernel_blacklist': [],
                       'lpae': False,
                       'fastboot': False}

arndale = {'device_type': 'arndale',
           'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                         'generic-arm-dtb-kernel-ci-kselftest-template.json'],
           'defconfig_blacklist': ['arm-allmodconfig'],
           'kernel_blacklist': [],
           'lpae': True,
           'fastboot': False}

snow = {'device_type': 'snow',
        'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                      'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                      'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                      'generic-arm-dtb-kernel-ci-kselftest-template.json'],
        'defconfig_blacklist': ['arm-allmodconfig'],
        'kernel_blacklist': [],
        'lpae': True,
        'fastboot': False}

arndale_octa = {'device_type': 'arndale-octa',
                'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                              'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                              'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                              'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                'defconfig_blacklist': ['arm-allmodconfig'],
                'kernel_blacklist': [],
                'lpae': True,
                'fastboot': False}

peach_pi = {'device_type': 'peach-pi',
            'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                          'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                          'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                          'generic-arm-dtb-kernel-ci-kselftest-template.json'],
            'defconfig_blacklist': ['arm-allmodconfig'],
            'kernel_blacklist': [],
            'lpae': True,
            'fastboot': False}

odroid_xu3 = {'device_type': 'odroid-xu3',
              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                            'generic-arm-dtb-kernel-ci-kselftest-template.json'],
              'defconfig_blacklist': ['arm-allmodconfig'],
              'kernel_blacklist': [],
              'lpae': True,
              'fastboot': False}

odroid_u2 = {'device_type': 'odroid-u2',
             'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                           'generic-arm-dtb-kernel-ci-kselftest-template.json'],
             'defconfig_blacklist': ['arm-allmodconfig'],
             'kernel_blacklist': [],
             'lpae': False,
             'fastboot': False}

odroid_x2 = {'device_type': 'odroid-x2',
             'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                           'generic-arm-dtb-kernel-ci-kselftest-template.json'],
             'defconfig_blacklist': ['arm-allmodconfig'],
             'kernel_blacklist': [],
             'lpae': False,
             'fastboot': False}

beaglebone_black = {'device_type': 'beaglebone-black',
                    'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                  'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                                  'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                                  'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                    'defconfig_blacklist': ['arm-allmodconfig'],
                    'kernel_blacklist': [],
                    'lpae': False,
                    'fastboot': False}

beagle_xm = {'device_type': 'beagle-xm',
             'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                           'generic-arm-dtb-kernel-ci-kselftest-template.json'],
             'defconfig_blacklist': ['arm-allmodconfig'],
             'kernel_blacklist': [],
             'lpae': False,
             'fastboot': False}

beagle_xm_legacy = {'device_type': 'beagle-xm',
                    'templates': ['generic-arm-kernel-ci-boot-template.json',
                                  'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                    'defconfig_blacklist': ['arm-allmodconfig'],
                    'kernel_blacklist': ['arm-soc',
                                         'next'],
                    'lpae': False,
                    'fastboot': False}

panda_es = {'device_type': 'panda-es',
            'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                          'generic-arm-dtb-kernel-ci-kselftest-template.json'],
            'defconfig_blacklist': ['arm-allmodconfig'],
            'kernel_blacklist': [],
            'lpae': False,
            'fastboot': False}

panda = {'device_type': 'panda',
         'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                       'generic-arm-dtb-kernel-ci-kselftest-template.json'],
         'defconfig_blacklist': ['arm-allmodconfig'],
         'kernel_blacklist': [],
         'lpae': False,
         'fastboot': False}

cubieboard3 = {'device_type': 'cubieboard3',
               'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                             'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                             'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                             'generic-arm-dtb-kernel-ci-cpufreq-ljt-stress-test-template.json',
                             'generic-arm-dtb-kernel-ci-kselftest-template.json'],
               'defconfig_blacklist': ['arm-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': True,
               'be': False,
               'fastboot': False}

cubieboard3_kvm = {'device_type': 'cubieboard3',
                   'templates': ['generic-arm-boot-kvm-template.json'],
                   'defconfig_blacklist': [],
                   'kernel_blacklist': [],
                   'lpae': True,
                   'fastboot': False}

hisi_x5hd2_dkb = {'device_type': 'hi3716cv200',
                  'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                                'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                                'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                  'defconfig_blacklist': ['arm-allmodconfig'],
                  'kernel_blacklist': [],
                  'lpae': False,
                  'fastboot': False}

d01 = {'device_type': 'd01',
       'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                     'generic-arm-dtb-kernel-ci-kselftest-template.json'],
       'defconfig_blacklist': ['arm-allmodconfig'],
       'kernel_blacklist': [],
       'lpae': True,
       'fastboot': False}

imx6q_wandboard = {'device_type': 'imx6q-wandboard',
                   'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                 'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                                 'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                                 'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig',
                                           'arm-allmodconfig'],
                   'kernel_blacklist': [],
                   'lpae': False,
                   'fastboot': False}

imx6q_sabrelite = {'device_type': 'imx6q-sabrelite',
                   'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                 'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                                 'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                                 'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                   'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                           'arm-multi_v5_defconfig',
                                           'arm-allmodconfig'],
                   'kernel_blacklist': [],
                   'lpae': False,
                   'fastboot': False}

utilite_pro = {'device_type': 'utilite-pro',
               'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                             'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                             'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                             'generic-arm-dtb-kernel-ci-kselftest-template.json'],
               'defconfig_blacklist': ['arm-imx_v4_v5_defconfig',
                                       'arm-multi_v5_defconfig',
                                       'arm-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': False,
               'fastboot': False}

snowball = {'device_type': 'snowball',
            'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                          'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                          'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                          'generic-arm-dtb-kernel-ci-kselftest-template.json'],
            'defconfig_blacklist': ['arm-allmodconfig'],
            'kernel_blacklist': [],
            'lpae': False,
            'fastboot': False}

ifc6540 = {'device_type': 'ifc6540',
           'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                         'generic-arm-dtb-kernel-ci-kselftest-template.json'],
           'defconfig_blacklist': ['arm-allmodconfig'],
           'kernel_blacklist': [],
           'lpae': False,
           'fastboot': True}

ifc6410 = {'device_type': 'ifc6410',
           'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                         'generic-arm-dtb-kernel-ci-kselftest-template.json'],
           'defconfig_blacklist': ['arm-allmodconfig'],
           'kernel_blacklist': [],
           'lpae': False,
           'fastboot': True}

sama53d = {'device_type': 'sama53d',
           'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                         'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                         'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                         'generic-arm-dtb-kernel-ci-kselftest-template.json'],
           'defconfig_blacklist': ['arm-at91_dt_defconfig',
                                   'arm-at91sam9260_9g20_defconfig',
                                   'arm-at91sam9g45_defconfig',
                                   'arm-allmodconfig'],
           'kernel_blacklist': [],
           'lpae': False,
           'fastboot': False}

jetson_tk1 = {'device_type': 'jetson-tk1',
              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                            'generic-arm-dtb-kernel-ci-kselftest-template.json'],
              'defconfig_blacklist': ['arm-allmodconfig'],
              'kernel_blacklist': [],
              'lpae': True,
              'fastboot': False}

tegra124_nyan_big = {'device_type': 'tegra124-nyan-big',
                     'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                   'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                                   'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                                   'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                     'defconfig_blacklist': ['arm-allmodconfig'],
                     'kernel_blacklist': [],
                     'lpae': True,
                     'fastboot': False}

parallella = {'device_type': 'parallella',
              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-mm-template.json',
                            'generic-arm-dtb-kernel-ci-ltp-syscalls-template.json',
                            'generic-arm-dtb-kernel-ci-kselftest-template.json'],
              'defconfig_blacklist': ['arm-allmodconfig'],
              'kernel_blacklist': [],
              'lpae': False,
              'fastboot': False}

optimus_a80 = {'device_type': 'optimus-a80',
               'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                             'generic-arm-dtb-kernel-ci-kselftest-template.json'],
               'defconfig_blacklist': ['arm-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': True,
               'fastboot': True}

cubieboard4 = {'device_type': 'cubieboard4',
               'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                             'generic-arm-dtb-kernel-ci-kselftest-template.json'],
               'defconfig_blacklist': ['arm-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': True,
               'fastboot': True}

qemu_arm_cortex_a9 = {'device_type': 'qemu-arm-cortex-a9',
                      'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                    'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                      'defconfig_blacklist': ['arm-allmodconfig'],
                      'kernel_blacklist': [],
                      'lpae': False,
                      'fastboot': False}

qemu_arm_cortex_a9_legacy = {'device_type': 'qemu-arm-cortex-a9',
                             'templates': ['generic-arm-kernel-ci-boot-template.json',
                                           'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                             'defconfig_blacklist': ['arm-allmodconfig'],
                             'kernel_blacklist': [],
                             'lpae': False,
                             'fastboot': False}

qemu_arm_cortex_a15_a7 = {'device_type': 'qemu-arm-cortex-a15',
                          'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                        'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                          'defconfig_blacklist': ['arm-allmodconfig'],
                          'kernel_blacklist': [],
                          'lpae': True,
                          'fastboot': False}

qemu_arm_cortex_a15 = {'device_type': 'qemu-arm-cortex-a15',
                       'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                     'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                       'defconfig_blacklist': ['arm-allmodconfig'],
                       'kernel_blacklist': [],
                       'lpae': True,
                       'fastboot': False}

qemu_arm_cortex_a15_legacy = {'device_type': 'qemu-arm-cortex-a15',
                              'templates': ['generic-arm-dtb-kernel-ci-boot-template.json',
                                            'generic-arm-dtb-kernel-ci-kselftest-template.json'],
                              'defconfig_blacklist': ['arm-allmodconfig'],
                              'kernel_blacklist': [],
                              'lpae': True,
                              'fastboot': False}

qemu_arm = {'device_type': 'qemu-arm',
            'templates': ['generic-arm-kernel-ci-boot-template.json',
                          'generic-arm-dtb-kernel-ci-kselftest-template.json'],
            'defconfig_blacklist': ['arm-allmodconfig'],
            'kernel_blacklist': ['v3.10',
                                 'lsk-v3.10',
                                 'v3.12',
                                 'lsk-v3.12'],
            'lpae': False,
            'fastboot': False}

qemu_aarch64 = {'device_type': 'qemu-aarch64',
                'templates': ['generic-arm64-kernel-ci-boot-template.json',
                              'generic-arm64-kernel-ci-kselftest-template.json'],
                'defconfig_blacklist': ['arm64-allnoconfig',
                                        'arm64-allmodconfig'],
                'kernel_blacklist': [],
                'lpae': False,
                'fastboot': False}

apm_mustang = {'device_type': 'mustang',
               'templates': ['generic-arm64-dtb-kernel-ci-boot-template.json',
                             'generic-arm64-dtb-kernel-ci-boot-be-template.json',
                             'generic-arm64-uboot-dtb-kernel-ci-ltp-mm-template.json',
                             'generic-arm64-uboot-dtb-kernel-ci-ltp-syscalls-template.json',
                             'generic-arm64-dtb-kernel-ci-kselftest-template.json'],
               'defconfig_blacklist': ['arm64-allnoconfig',
                                       'arm64-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': False,
               'fastboot': False}

apm_mustang_kvm = {'device_type': 'mustang',
                   'templates': ['generic-arm64-boot-kvm-template.json'],
                   'defconfig_blacklist': ['arm64-allnoconfig',
                                           'arm64-allmodconfig'],
                   'kernel_blacklist': ['v3.10',
                                        'lsk-v3.10',
                                        'v3.12',
                                        'lsk-v3.12',
                                        'v3.14',
                                        'lsk-v3.14',
                                        'v3.18',
                                        'lsk-v3.18'],
                   'lpae': False,
                   'fastboot': False}

juno = {'device_type': 'juno',
        'templates': ['juno-arm64-dtb-kernel-ci-boot-template.json',
                      'juno-arm64-dtb-kernel-ci-ltp-mm-template.json',
                      'juno-arm64-dtb-kernel-ci-kselftest-template.json'],
        'defconfig_blacklist': ['arm64-allnoconfig',
                                'arm64-allmodconfig'],
        'kernel_blacklist': [],
        'lpae': False,
        'fastboot': False}

fvp_aemv8a = {'device_type': 'rtsm_fvp_base-aemv8a',
              'templates': ['generic-arm64-dtb-uefi-kernel-ci-boot-template.json',
                            'generic-arm64-dtb-kernel-ci-kselftest-template.json'],
              'defconfig_blacklist': ['arm64-allnoconfig',
                                      'arm64-allmodconfig',
                                      'arm64-defconfig+kvm-host',
                                      'arm64-defconfig+kvm-guest'],
              'kernel_blacklist': [],
              'lpae': False,
              'fastboot': False}

juno_kvm = {'device_type': 'juno',
            'templates': ['generic-arm64-boot-kvm-template.json'],
            'defconfig_blacklist': ['arm64-allnoconfig',
                                    'arm64-allmodconfig'],
            'kernel_blacklist': ['v3.10',
                                 'lsk-v3.10',
                                 'v3.12',
                                 'lsk-v3.12',
                                 'v3.14',
                                 'lsk-v3.14',
                                 'v3.18',
                                 'lsk-v3.18'],
            'lpae': False,
            'fastboot': False}

hi6220_hikey = {'device_type': 'hi6220-hikey',
                'templates': ['generic-arm64-dtb-kernel-ci-boot-template.json',
                              'generic-arm64-dtb-kernel-ci-kselftest-template.json'],
                'defconfig_blacklist': ['arm64-allnoconfig',
                                        'arm64-allmodconfig'],
               'kernel_blacklist': [],
               'lpae': False,
               'be': False,
               'fastboot': False}


x86 = {'device_type': 'x86',
       'templates': ['generic-x86-kernel-ci-boot-template.json',
                     'generic-x86-kernel-ci-kselftest-template.json'],
       'defconfig_blacklist': ['x86-i386_defconfig',
                               'x86-allnoconfig',
                               'x86-allmodconfig',
                               'x86-tinyconfig',
                               'x86-kvm_guest.config'],
       'kernel_blacklist': [],
       'lpae': False,
       'fastboot': False}

minnowboard_max_E3825 = {'device_type': 'minnowboard-max-E3825',
                         'templates': ['generic-x86-kernel-ci-boot-template.json',
                                       'generic-x86-kernel-ci-kselftest-template.json'],
                         'defconfig_blacklist': ['x86-i386_defconfig',
                                                 'x86-allnoconfig',
                                                 'x86-allmodconfig',
                                                 'x86-tinyconfig',
                                                 'x86-kvm_guest.config'],
                         'kernel_blacklist': [],
                         'lpae': False,
                         'fastboot': False}

x86_kvm = {'device_type': 'kvm',
           'templates': ['generic-x86-kernel-ci-boot-template.json',
                         'generic-x86-kernel-ci-kselftest-template.json'],
           'defconfig_blacklist': ['x86-i386_defconfig',
                                   'x86-allnoconfig',
                                   'x86-allmodconfig',
                                   'x86-tinyconfig',
                                   'x86-kvm_guest.config'],
           'kernel_blacklist': [],
           'lpae': False,
           'fastboot': False}

device_map = {'bcm2835-rpi-b-plus.dtb': [bcm2835_rpi_b_plus],
              'armada-370-mirabox.dtb': [armada_370_mirabox],
              'exynos5250-arndale.dtb': [arndale],
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
              'sun7i-a20-cubietruck.dtb': [cubieboard3, cubieboard3_kvm],
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
              'tegra124-nyan-big.dtb': [tegra124_nyan_big],
              'zynq-parallella.dtb': [parallella],
              'sun9i-a80-optimus.dtb': [optimus_a80],
              'sun9i-a80-cubieboard4.dtb': [cubieboard4],
              'vexpress-v2p-ca15-tc1.dtb': [qemu_arm_cortex_a15],
              'vexpress-v2p-ca15-tc1-legacy': [qemu_arm_cortex_a15_legacy],
              'vexpress-v2p-ca15_a7.dtb': [qemu_arm_cortex_a15_a7],
              'vexpress-v2p-ca9.dtb': [qemu_arm_cortex_a9],
              'vexpress-v2p-ca9-legacy': [qemu_arm_cortex_a9_legacy],
              'qemu-arm-legacy': [qemu_arm],
              'qemu-aarch64-legacy': [qemu_aarch64],
              'apm-mustang.dtb': [apm_mustang, apm_mustang_kvm],
              'juno.dtb': [juno, juno_kvm],
              'fvp-base-gicv2-psci.dtb': [fvp_aemv8a],
              'hi6220-hikey.dtb': [hi6220_hikey],
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


def create_jobs(base_url, kernel, plans, platform_list, targets):
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
                elif defconfig in device['defconfig_blacklist']:
                    print '%s has been blacklisted. Skipping JSON creation' % defconfig
                elif any([x for x in device['kernel_blacklist'] if x in kernel_version]):
                    print '%s has been blacklisted. Skipping JSON creation' % kernel_version
                elif targets is not None and device_type not in targets:
                    print '%s device type has been omitted. Skipping JSON creation.' % device_type
                elif not any([x for x in defconfigs if x == defconfig]) and plan != 'boot':
                    print '%s has been omitted from the %s test plan. Skipping JSON creation.' % (defconfig, plan)
                else:
                        for template in device_templates:
                            job_name = tree + '-' + kernel_version + '-' + defconfig[:100] + '-' + platform_name + '-' + device_type + '-' + plan
                            job_json = cwd + '/jobs/' + job_name + '.json'
                            template_file = cwd + '/templates/' + plan + '/' + str(template)
                            if os.path.exists(template_file):
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
                                            dummy_modules_url = 'http://images.armcloud.us/lava/common/modules.tar.xz'
                                            if any([x for x in no_modules_list if x in defconfig]):
                                                # Dummy Modules
                                                tmp = tmp.replace('{modules_url}', dummy_modules_url)
                                            else:
                                                tmp = tmp.replace('{modules_url}', modules_url)
                                            tmp = tmp.replace('{tree}', tree)
                                            if platform_name.endswith('.dtb'):
                                                tmp = tmp.replace('{device_tree}', platform_name)
                                            tmp = tmp.replace('{kernel_version}', kernel_version)
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
                                            fout.write(tmp)
                                print 'JSON Job created: jobs/%s' % job_name


def walk_url(url, plans=None, arch=None, targets=None):
    global base_url
    global kernel
    global platform_list
    global legacy_platform_list

    try:
        html = urllib2.urlopen(url, timeout=30).read()
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
            print 'Found artifacts at: %s' % base_url
            create_jobs(base_url, kernel, plans, platform_list, targets)
            # Hack for subdirectories with arm64 dtbs
            if 'arm64' not in base_url:
                base_url = None
                kernel = None
            platform_list = []
        elif legacy_platform_list:
            print 'Found artifacts at: %s' % base_url
            create_jobs(base_url, kernel, plans, legacy_platform_list, targets)
            legacy_platform_list = []

    for dir in dirs:
        walk_url(url + dir, plans, arch, targets)

def main(args):
    setup_job_dir(os.getcwd() + '/jobs')
    print 'Scanning %s for kernel information...' % args.url
    walk_url(args.url, args.plans, args.arch, args.targets)
    print 'Done scanning for kernel information'
    print 'Done creating JSON jobs'
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="url to build artifacts")
    parser.add_argument("--plans", nargs='+', required=True, help="test plan to create jobs for")
    parser.add_argument("--arch", help="specific architecture to create jobs for")
    parser.add_argument("--targets", nargs='+', help="specific targets to create jobs for")
    args = parser.parse_args()
    main(args)
