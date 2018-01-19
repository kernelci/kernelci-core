#!/usr/bin/python
#
# Copyright (C) 2014, 2015, 2016, 2017 Linaro Limited
# Author: Anders Roxell <anders.roxell@linaro.org>
# Author: Matt Hart <matthew.hart@linaro.org>
# Author: Tyler Baker <tyler.baker@linaro.org>
#
# Copyright (C) 2015 Baylibre SAS
# Author: Kevin Hilman <khilman@baylibre.com>
# Author: Marc Titinger <mtitinger@baylibre.com>
#
# Copyright (C) 2016, 2017 Free Electrons
# Author: Florent Jacquet <florent.jacquet@free-electrons.com>
# Author: Quentin Schulz <quentin.schulz@free-electrons.com>
#
# Copyright (C) 2016, 2017 Pengutronix
# Author: Jan Luebbe <jlu@pengutronix.de>
# Author: Michael Grzeschik <m.grzeschik@pengutronix.de>
#
# Copyright (C) 2016 Collabora Limited
# Author: Sjoerd Simons <sjoerd.simons@collabora.co.uk>
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

# <variable> = required
# Usage ./lava-report.py <option> [json]
import os
import urlparse
import xmlrpclib
import json
import argparse
import time
import subprocess
import re
import urllib2
import requests

from lib import configuration
from lib import utils

log2html = 'https://git.linaro.org/people/kevin.hilman/build-scripts.git/blob_plain/HEAD:/log2html.py'

device_map = {'alpine-db': ['alpine-db', 'alpine'],
              'alpine-v2-evp': ['alpine-v2-evp', 'alpine'],
              'bcm2835-rpi-b-plus': ['bcm2835-rpi-b-plus', 'bcm'],
              'bcm2836-rpi-2-b' : [ 'bcm2836-rpi-2-b', 'bcm'],
              'bcm4708-smartrg-sr400ac': ['bcm4708-smartrg-sr400ac', 'bcm'],
              'armada-370-db': ['armada-370-db', 'mvebu'],
              'armada-370-mirabox': ['armada-370-mirabox', 'mvebu'],
              'armada-xp-openblocks-ax3-4': ['armada-xp-openblocks-ax3-4', 'mvebu'],
              'kirkwood-openblocks_a7': ['kirkwood-openblocks_a7', 'mvebu'],
              'armada-xp-linksys-mamba': ['armada-xp-linksys-mamba', 'mvebu'],
              'armada-370-rd': ['armada-370-rd', 'mvebu'],
              'armada-375-db': ['armada-375-db', 'mvebu'],
              'armada-385-db-ap': ['armada-385-db-ap', 'mvebu'],
              'armada-388-clearfog': ['armada-388-clearfog', 'mvebu'],
              'armada-388-gp': ['armada-388-gp', 'mvebu'],
              'armada-398-db': ['armada-398-db', 'mvebu'],
              'kirkwood-db-88f6282': ['kirkwood-db-88f6282', 'mvebu'],
              'armada-3720-db': ['armada-3720-db', 'mvebu'],
              'armada-7040-db': ['armada-7040-db', 'mvebu'],
              'armada-8040-db': ['armada-8040-db', 'mvebu'],
              'armada-xp-db': ['armada-xp-db', 'mvebu'],
              'armada-xp-gp': ['armada-xp-gp', 'mvebu'],
              'orion5x_rd88f5182_nas': ['orion5x_rd88f5182_nas', 'mvebu'],
              'dove-cubox': ['dove-cubox', 'mvebu'],
              'arndale': ['exynos5250-arndale', 'exynos'],
              'snow': ['exynos5250-snow', 'exynos'],
              'arndale-octa': ['exynos5420-arndale-octa','exynos'],
              'peach-pi': ['exynos5800-peach-pi', 'exynos'],
              'odroid-xu3': ['exynos5422-odroidxu3', 'exynos'],
              'odroid-u2': ['exynos4412-odroidu3', 'exynos'],
              'odroid-x2': ['exynos4412-odroidx2', 'exynos'],
              'beaglebone-black': ['am335x-boneblack', 'omap2'],
              'omap3-overo-tobi': ['omap3-overo-tobi', 'omap2'],
              'omap3-overo-storm-tobi': ['omap3-overo-storm-tobi', 'omap2'],
              'beagle-xm': ['omap3-beagle-xm', 'omap2'],
              'panda-es': ['omap4-panda-es', 'omap2'],
              'panda': ['omap4-panda', 'omap2'],
              'omap5-uevm' : ['omap5-uevm', 'omap2' ],
              'cubieboard2': ['sun7i-a20-cubieboard2', 'sunxi'],
              'cubieboard3': ['sun7i-a20-cubietruck', 'sunxi'],
              'cubieboard3-kvm-host': ['sun7i-a20-cubietruck-kvm-host', 'sunxi'],
              'cubieboard3-kvm-guest': ['sun7i-a20-cubietruck-kvm-guest', 'sunxi'],
              'sun7i-a20-bananapi': ['sun7i-a20-bananapi', 'sunxi'],
              'optimus-a80': ['sun9i-a80-optimus', 'sunxi'],
              'cubieboard4': ['sun9i-a80-cubieboard4', 'sunxi'],
              'sun5i-gr8-chip-pro': ['sun5i-gr8-chip-pro', 'sunxi'],
              'sun5i-r8-chip': ['sun5i-r8-chip', 'sunxi'],
              'sun8i-a23-evb': ['sun8i-a23-evb', 'sunxi'],
              'sun8i-a33-sinlinx-sina33': ['sun8i-a33-sinlinx-sina33', 'sunxi'],
              'sun8i-a83t-allwinner-h8homlet-v2': ['sun8i-a83t-allwinner-h8homlet-v2', 'sunxi'],
              'sun8i-h3-orangepi-pc': ['sun8i-h3-orangepi-pc', 'sunxi'],
              'rk3288-rock2-square': ['rk3288-rock2-square', 'rockchip'],
              'rk3399-puma-haikou': ['rk3399-puma-haikou', 'rockchip'],
              'zx296702-ad1': ['zx296702-ad1', 'sunxi'],
              'hi3716cv200': ['hisi-x5hd2-dkb', 'hisi'],
              'd01': ['hip04-d01', 'hisi'],
              'imx6ul-pico-hobbit': ['imx6ul-pico-hobbit', 'imx'],
              'imx6q-wandboard': ['imx6q-wandboard', 'imx'],
              'imx6q-sabrelite': ['imx6q-sabrelite', 'imx'],
              'meson8b_odroidc1': ['meson8b-odroidc1', 'meson'],
              'meson-gxbb-odroidc2': ['meson-gxbb-odroidc2', 'amlogic'],
              'meson-gxbb-p200': ['meson-gxbb-p200', 'amlogic'],
              'imx6dl-riotboard': ['imx6dl-riotboard', 'imx'],
              'imx53-qsbr': ['imx53-qsrb', 'imx'],
              'imx28-duckbill': ['imx28-duckbill', 'imx'],
              'imx23-olinuxino': ['imx23-olinuxino', 'imx'],
              'imx27-phytec-phycard-s-rdk': ['imx27-phytec-phycard-s-rdk', 'imx'],
              'utilite-pro': ['imx6q-cm-fx6', 'imx'],
              'imx6q-nitrogen6x': ['imx6q-nitrogen6x', 'imx'],
              'snowball': ['ste-snowball', 'u8500'],
              'ifc6540': ['qcom-apq8084-ifc6540', 'qcom'],
              'ifc6410': ['qcom-apq8064-ifc6410', 'qcom'],
              'socfpga-cyclone5-socrates': ['socfpga_cyclone5_socrates', 'socfpga'],
              'highbank': ['highbank', 'highbank'],
              'sama53d': ['at91-sama5d3_xplained', 'at91'],
              'sama5d34ek': ['sama5d34ek', 'at91'],
              'sama5d36ek': ['sama5d36ek', 'at91'],
              'sama5d35ek': ['sama5d35ek', 'at91'],
              'at91sam9m10g45ek': ['at91sam9m10g45ek', 'at91'],
              'at91sam9261ek': ['at91sam9261ek', 'at91'],
              'at91sam9x25ek': ['at91sam9x25ek', 'at91'],
              'at91sam9x35ek': ['at91sam9x35ek', 'at91'],
              'at91rm9200ek': ['at91rm9200ek', 'at91'],
              'at91-sama5d2_xplained': ['at91-sama5d2_xplained', 'at91'],
              'at91-sama5d4_xplained': ['at91-sama5d4_xplained', 'at91'],
              'jetson-tk1': ['tegra124-jetson-tk1', 'tegra'],
              'tegra124-nyan-big': ['tegra124-nyan-big', 'tegra'],
              'parallella': ['zynq-parallella', 'zynq'],
              'zynq-zc702': ['zynq-zc702', 'zynq'],
              'vf610-zii-dev-rev-b': ['vf610-zii-dev-rev-b', 'imx'],
              'qemu-arm-cortex-a15': ['vexpress-v2p-ca15-tc1', 'vexpress'],
              'qemu-arm-cortex-a15-a7': ['vexpress-v2p-ca15_a7', 'vexpress'],
              'qemu-arm-cortex-a9': ['vexpress-v2p-ca9', 'vexpress'],
              'qemu-arm': ['versatilepb', 'versatile'],
              'qemu-aarch64': ['qemu-aarch64', 'qemu'],
              'apq8016-sbc': ['apq8016-sbc', 'qcom'],
              'mustang': ['apm-mustang', 'apm'],
              'mustang-kvm-host': ['apm-mustang-kvm-host', 'apm'],
              'mustang-kvm-guest': ['apm-mustang-kvm-guest', 'apm'],
              'mustang-kvm-uefi-host': ['apm-mustang-kvm-uefi-host', 'apm'],
              'mustang-kvm-uefi-guest': ['apm-mustang-kvm-uefi-guest', 'apm'],
              'juno': ['juno', 'arm'],
              'juno-kvm-host': ['juno-kvm-host', 'arm'],
              'juno-kvm-guest': ['juno-kvm-guest', 'arm'],
              'juno-kvm-uefi-host': ['juno-kvm-uefi-host', 'arm'],
              'juno-kvm-uefi-guest': ['juno-kvm-uefi-guest', 'arm'],
              'rtsm_fvp_base-aemv8a': ['fvp-base-gicv2-psci', 'arm'],
              'hi6220-hikey': ['hi6220-hikey', 'hisi'],
              'fsl-ls2085a-rdb': ['fsl-ls2080a-rdb', 'freescale'],
              'fsl-ls2085a-simu': ['fsl-ls2080a-simu', 'freescale'],
              'r8a7795-salvator-x': ['r8a7795-salvator-x', 'renesas'],
              'da850-lcdk': ['da850-lcdk', 'davinci'],
              'minnowboard-max-E3825': ['minnowboard-max', None],
              'x86-atom330': ['x86-atom330', None],
              'x86': ['x86', None],
              'kvm': ['x86-kvm', None],
              'qemu-i386': ['qemu-i386', None]}


def download_log2html(url):
    print 'Fetching latest log2html script'
    try:
        response = urllib2.urlopen(url, timeout=30)
    except IOError, e:
        print 'error fetching %s: %s' % (url, e)
        exit(1)
    script = response.read()
    utils.write_file(script, 'log2html.py', os.getcwd())


def parse_json(json):
    jobs = utils.load_json(json)
    url = utils.validate_input(jobs['username'], jobs['token'], jobs['server'])
    connection = utils.connect(url)
    duration = jobs['duration']
    # Remove unused data
    jobs.pop('duration')
    jobs.pop('username')
    jobs.pop('token')
    jobs.pop('server')
    return connection, jobs, duration


def push(method, url, data, headers):
    retry = True
    while retry:
        if method == 'POST':
            response = requests.post(url, data=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, data=data, headers=headers)
        else:
            print "ERROR: unsupported method"
            exit(1)
        if response.status_code != 500:
            retry = False
            print "OK"
        else:
            time.sleep(10)
            print response.content


def boot_report(config):
    connection, jobs, duration =  parse_json(config.get("boot"))
    # TODO: Fix this when multi-lab sync is working
    #download_log2html(log2html)
    results_directory = os.getcwd() + '/results'
    results = {}
    dt_tests = False
    utils.mkdir(results_directory)
    for job_id in jobs:
        print 'Job ID: %s' % job_id
        # Init
        boot_meta = {}
        api_url = None
        arch = None
        board_instance = None
        boot_retries = 0
        kernel_defconfig = None
        kernel_defconfig_base = None
        kernel_version = None
        device_tree = None
        kernel_endian = None
        kernel_tree = None
        git_branch = None
        kernel_addr = None
        initrd_addr = None
        dtb_addr = None
        dtb_append = None
        fastboot = None
        fastboot_cmd = None
        test_plan = None
        job_file = ''
        dt_test = None
        dt_test_result = None
        dt_tests_passed = None
        dt_tests_failed = None
        board_offline = False
        kernel_boot_time = None
        boot_failure_reason = None
        efi_rtc = False
        # Retrieve job details
        job_details = connection.scheduler.job_details(job_id)
        if job_details['requested_device_type_id']:
            device_type = job_details['requested_device_type_id']
        if job_details['description']:
            job_name = job_details['description']
        result = jobs[job_id]['result']
        bundle = jobs[job_id]['bundle']
        if bundle is None and device_type == 'dynamic-vm':
            host_job_id = job_id.replace('.1', '.0')
            bundle = jobs[host_job_id]['bundle']
            if bundle is None:
                print '%s bundle is empty, skipping...' % device_type
                continue
        # Retrieve the log file
        try:
            binary_job_file = connection.scheduler.job_output(job_id)
        except xmlrpclib.Fault:
            print 'Job output not found for %s' % device_type
            continue
        # Parse LAVA messages out of log
        raw_job_file = str(binary_job_file)
        for line in raw_job_file.splitlines():
            if 'Infrastructure Error:' in line:
                print 'Infrastructure Error detected!'
                index = line.find('Infrastructure Error:')
                boot_failure_reason = line[index:]
                board_offline = True
            if 'Bootloader Error:' in line:
                print 'Bootloader Error detected!'
                index = line.find('Bootloader Error:')
                boot_failure_reason = line[index:]
                board_offline = True
            if 'Kernel Error:' in line:
                print 'Kernel Error detected!'
                index = line.find('Kernel Error:')
                boot_failure_reason = line[index:]
            if 'Userspace Error:' in line:
                print 'Userspace Error detected!'
                index = line.find('Userspace Error:')
                boot_failure_reason = line[index:]
            if '<LAVA_DISPATCHER>' not in line:
                if len(line) != 0:
                    job_file += line + '\n'
            if '### dt-test ### end of selftest' in line:
                dt_tests = True
                regex = re.compile("(?P<test>\d+\*?)")
                dt_test_results = regex.findall(line)
                if len(dt_test_results) > 2:
                    dt_tests_passed = dt_test_results[2]
                    dt_tests_failed = dt_test_results[3]
                else:
                    dt_tests_passed = dt_test_results[0]
                    dt_tests_failed = dt_test_results[1]
                if int(dt_tests_failed) > 0:
                    dt_test_result = 'FAIL'
                else:
                    dt_test_result = 'PASS'
            if 'rtc-efi rtc-efi: setting system clock to' in line:
                if device_type == 'dynamic-vm':
                    efi_rtc = True
        # Retrieve bundle
        if bundle is not None:
            json_bundle = connection.dashboard.get(bundle)
            bundle_data = json.loads(json_bundle['content'])
            # Get the boot data from LAVA
            for test_results in bundle_data['test_runs']:
                # Check for the LAVA self boot test
                if test_results['test_id'] == 'lava':
                    for test in test_results['test_results']:
                        # TODO for compat :(
                        if test['test_case_id'] == 'kernel_boot_time':
                            kernel_boot_time = test['measurement']
                        if test['test_case_id'] == 'test_kernel_boot_time':
                            kernel_boot_time = test['measurement']
                    bundle_attributes = bundle_data['test_runs'][-1]['attributes']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.defconfig'):
                print bundle_attributes['kernel.defconfig']
            if utils.in_bundle_attributes(bundle_attributes, 'target'):
                board_instance = bundle_attributes['target']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.defconfig'):
                kernel_defconfig = bundle_attributes['kernel.defconfig']
                kernel_defconfig_base = ''.join(kernel_defconfig.split('+')[:1])
            if utils.in_bundle_attributes(bundle_attributes, 'arch'):
                arch = bundle_attributes['arch']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.describe'):
                kernel_version = bundle_attributes['kernel.describe']
            if utils.in_bundle_attributes(bundle_attributes, 'device.tree'):
                device_tree = bundle_attributes['device.tree']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.endian'):
                kernel_endian = bundle_attributes['kernel.endian']
            if utils.in_bundle_attributes(bundle_attributes, 'platform.fastboot'):
                fastboot = bundle_attributes['platform.fastboot']
            if kernel_boot_time is None:
                if utils.in_bundle_attributes(bundle_attributes, 'kernel-boot-time'):
                    kernel_boot_time = bundle_attributes['kernel-boot-time']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.tree'):
                kernel_tree = bundle_attributes['kernel.tree']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel-addr'):
                kernel_addr = bundle_attributes['kernel-addr']
            if utils.in_bundle_attributes(bundle_attributes, 'initrd-addr'):
                initrd_addr = bundle_attributes['initrd-addr']
            if utils.in_bundle_attributes(bundle_attributes, 'dtb-addr'):
                dtb_addr = bundle_attributes['dtb-addr']
            if utils.in_bundle_attributes(bundle_attributes, 'dtb-append'):
                dtb_append = bundle_attributes['dtb-append']
            if utils.in_bundle_attributes(bundle_attributes, 'boot_retries'):
                boot_retries = int(bundle_attributes['boot_retries'])
            if utils.in_bundle_attributes(bundle_attributes, 'test.plan'):
                test_plan = bundle_attributes['test.plan']
            if utils.in_bundle_attributes(bundle_attributes, 'kernel.branch'):
                git_branch = bundle_attributes['kernel.branch']

        # Check if we found efi-rtc
        if test_plan == 'boot-kvm-uefi' and not efi_rtc:
            if device_type == 'dynamic-vm':
                boot_failure_reason = 'Unable to read EFI rtc'
                result = 'FAIL'
        # Record the boot log and result
        # TODO: Will need to map device_types to dashboard device types
        if kernel_defconfig and device_type and result:
            if (arch == 'arm' or arch =='arm64') and device_tree is None:
                platform_name = device_map[device_type][0] + ',legacy'
            else:
                if device_tree == 'vexpress-v2p-ca15_a7.dtb':
                    platform_name = 'vexpress-v2p-ca15_a7'
                elif device_tree == 'fsl-ls2080a-simu.dtb':
                    platform_name = 'fsl-ls2080a-simu'
                elif test_plan == 'boot-kvm' or test_plan == 'boot-kvm-uefi':
                    if device_tree == 'sun7i-a20-cubietruck.dtb':
                        if device_type == 'dynamic-vm':
                            device_type = 'cubieboard3-kvm-guest'
                            platform_name = device_map[device_type][0]
                        else:
                            device_type = 'cubieboard3-kvm-host'
                            platform_name = device_map[device_type][0]
                    elif device_tree == 'apm-mustang.dtb':
                        if device_type == 'dynamic-vm':
                            if test_plan == 'boot-kvm-uefi':
                                device_type = 'mustang-kvm-uefi-guest'
                            else:
                                device_type = 'mustang-kvm-guest'
                            platform_name = device_map[device_type][0]
                        else:
                            if test_plan == 'boot-kvm-uefi':
                                device_type = 'mustang-kvm-uefi-host'
                            else:
                                device_type = 'mustang-kvm-host'
                            platform_name = device_map[device_type][0]
                    elif device_tree == 'juno.dtb':
                        if device_type == 'dynamic-vm':
                            if test_plan == 'boot-kvm-uefi':
                                device_type = 'juno-kvm-uefi-guest'
                            else:
                                device_type = 'juno-kvm-guest'
                            platform_name = device_map[device_type][0]
                        else:
                            if test_plan == 'boot-kvm-uefi':
                                device_type = 'juno-kvm-uefi-host'
                            else:
                                device_type = 'juno-kvm-host'
                            platform_name = device_map[device_type][0]
                elif test_plan == 'boot-nfs' or test_plan == 'boot-nfs-mp':
                    platform_name = device_map[device_type][0] + '_rootfs:nfs'
                else:
                    platform_name = device_map[device_type][0]
            print 'Creating boot log for %s' % platform_name
            log = 'boot-%s.txt' % platform_name
            html = 'boot-%s.html' % platform_name
            if config.get("lab"):
                directory = os.path.join(results_directory, kernel_defconfig + '/' + config.get("lab"))
            else:
                directory = os.path.join(results_directory, kernel_defconfig)
            utils.ensure_dir(directory)
            utils.write_file(job_file, log, directory)
            if kernel_boot_time is None:
                kernel_boot_time = '0.0'
            if results.has_key(kernel_defconfig):
                results[kernel_defconfig].append({'device_type': platform_name, 'dt_test_result': dt_test_result, 'dt_tests_passed': dt_tests_passed, 'dt_tests_failed': dt_tests_failed, 'kernel_boot_time': kernel_boot_time, 'result': result})
            else:
                results[kernel_defconfig] = [{'device_type': platform_name, 'dt_test_result': dt_test_result, 'dt_tests_passed': dt_tests_passed, 'dt_tests_failed': dt_tests_failed, 'kernel_boot_time': kernel_boot_time, 'result': result}]
            # Create JSON format boot metadata
            print 'Creating JSON format boot metadata'
            if config.get("lab"):
                boot_meta['lab_name'] = config.get("lab")
            else:
                boot_meta['lab_name'] = None
            if board_instance:
                boot_meta['board_instance'] = board_instance
            boot_meta['retries'] = boot_retries
            boot_meta['boot_log'] = log
            boot_meta['boot_log_html'] = html
            # TODO: Fix this
            boot_meta['version'] = '1.1'
            boot_meta['arch'] = arch
            boot_meta['defconfig'] = kernel_defconfig_base
            boot_meta['defconfig_full'] = kernel_defconfig
            if device_map[device_type][1]:
                boot_meta['mach'] = device_map[device_type][1]
            boot_meta['kernel'] = kernel_version
            boot_meta['git_branch'] = git_branch
            boot_meta['job'] = kernel_tree
            boot_meta['board'] = platform_name
            if board_offline and result == 'FAIL':
                boot_meta['boot_result'] = 'OFFLINE'
                #results[kernel_defconfig]['result'] = 'OFFLINE'
            else:
                boot_meta['boot_result'] = result
            if result == 'FAIL' or result == 'OFFLINE':
                if boot_failure_reason:
                    boot_meta['boot_result_description'] = boot_failure_reason
                else:
                    boot_meta['boot_result_description'] = 'Unknown Error: platform failed to boot'
            boot_meta['boot_time'] = kernel_boot_time
            # TODO: Fix this
            boot_meta['boot_warnings'] = None
            if device_tree:
                if arch == 'arm64':
                    boot_meta['dtb'] = 'dtbs/' + device_map[device_type][1] + '/' + device_tree
                else:
                    boot_meta['dtb'] = 'dtbs/' + device_tree
            else:
                boot_meta['dtb'] = device_tree
            boot_meta['dtb_addr'] = dtb_addr
            boot_meta['dtb_append'] = dtb_append
            boot_meta['dt_test'] = dt_test
            boot_meta['endian'] = kernel_endian
            boot_meta['fastboot'] = fastboot
            # TODO: Fix this
            boot_meta['initrd'] = None
            boot_meta['initrd_addr'] = initrd_addr
            if arch == 'arm':
                boot_meta['kernel_image'] = 'zImage'
            elif arch == 'arm64':
                boot_meta['kernel_image'] = 'Image'
            else:
                boot_meta['kernel_image'] = 'bzImage'
            boot_meta['loadaddr'] = kernel_addr
            json_file = 'boot-%s.json' % platform_name
            utils.write_json(json_file, directory, boot_meta)
            print 'Creating html version of boot log for %s' % platform_name
            cmd = 'python log2html.py %s' % os.path.join(directory, log)
            subprocess.check_output(cmd, shell=True)
            if config.get("lab") and config.get("api") and config.get("token"):
                print 'Sending boot result to %s for %s' % (config.get("api"), platform_name)
                headers = {
                    'Authorization': config.get("token"),
                    'Content-Type': 'application/json'
                }
                api_url = urlparse.urljoin(config.get("api"), '/boot')
                push('POST', api_url, data=json.dumps(boot_meta), headers=headers)
                headers = {
                    'Authorization': config.get("token"),
                }
                print 'Uploading text version of boot log'
                with open(os.path.join(directory, log)) as lh:
                    data = lh.read()
                api_url = urlparse.urljoin(config.get("api"), '/upload/%s/%s/%s/%s/%s/%s/%s' % (kernel_tree,
                                                                                 git_branch,
                                                                                 kernel_version,
                                                                                 arch,
                                                                                 kernel_defconfig,
                                                                                 config.get("lab"),
                                                                                 log))
                push('PUT', api_url, data=data, headers=headers)
                print 'Uploading html version of boot log'
                with open(os.path.join(directory, html)) as lh:
                    data = lh.read()
                api_url = urlparse.urljoin(config.get("api"), '/upload/%s/%s/%s/%s/%s/%s/%s' % (kernel_tree,
                                                                                 git_branch,
                                                                                 kernel_version,
                                                                                 arch,
                                                                                 kernel_defconfig,
                                                                                 config.get("lab"),
                                                                                 html))
                push('PUT', api_url, data=data, headers=headers)


def main(args):
    config = configuration.get_config(args)

    if config.get("boot"):
        boot_report(config)
    exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration for the LAVA server")
    parser.add_argument("--section", default="default", help="section in the LAVA config file")
    parser.add_argument("--boot", help="creates a kernel-ci boot report from a given json file")
    parser.add_argument("--lab", help="lab id")
    parser.add_argument("--api", help="api url")
    parser.add_argument("--token", help="authentication token")
    args = vars(parser.parse_args())
    main(args)
