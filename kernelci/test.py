# Copyright (C) 2019 Collabora Limited
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

import os
import urllib.parse


def match_configs(configs, bmeta, dtbs, lab):
    """Filter the test configs for a given kernel build and lab.

    *configs* is a list of all the initial test configs
    *bmeta* is a dictionary with the kernel build meta-data
    *dtbs* is the list of dtb files included in the kernel build
    *lab* is a Lab object instance

    The returned value is a list with a subset of the configs that match the
    provided kernel build meta-data and lab filters.
    """
    defconfig = bmeta['defconfig_full']
    arch = bmeta['arch']

    filters = {
        'arch': arch,
        'defconfig': defconfig,
        'kernel': bmeta['git_describe'],
        'build_environment': bmeta['build_environment'],
        'tree': bmeta['job'],
        'branch': bmeta['git_branch'],
    }

    flags = {
        'big_endian': 'BIG_ENDIAN' in defconfig,
        'lpae': 'LPAE' in defconfig,
    }

    match = set()

    for test_config in configs:
        if not test_config.match(arch, flags, filters):
            continue
        dtb = test_config.device_type.dtb
        if dtb and dtb not in dtbs:
            continue
        for plan_name, plan in test_config.test_plans.items():
            if not plan.match(filters):
                continue
            filters['plan'] = plan_name
            if lab.match(filters):
                match.add((test_config.device_type, plan))

    return match


def get_params(bmeta, target, plan_config, storage):
    """Get a dictionary with all the test parameters to run a test job

    *bmeta* is a dictionary with the kernel build meta-data
    *target* is the name of the target platform to run the test
    *plan_config* is a TestPlan object for the test plan to run
    *storage* is the URL of the storage server
    """
    arch = target.arch
    dtb = dtb_full = target.dtb
    dtb_dir = bmeta.get("dtb_dir", "")
    if dtb:
        dtb = dtb_full = os.path.join(dtb_dir, target.dtb)
        dtb = os.path.basename(dtb)  # hack for dtbs in subfolders
    file_server_resource = bmeta['file_server_resource']
    job_px = file_server_resource.replace('/', '-')
    url_px = file_server_resource
    job_name = '-'.join([job_px, dtb or 'no-dtb',
                         target.name, plan_config.name])
    base_url = urllib.parse.urljoin(storage, '/'.join([url_px, '']))
    kernel_img = bmeta['kernel_image']
    kernel_url = urllib.parse.urljoin(storage, '/'.join([url_px, kernel_img]))
    if dtb_full and dtb_full.endswith('.dtb'):
        dtb_url = urllib.parse.urljoin(
            storage, '/'.join([url_px, dtb_full]))
    else:
        dtb_url = None
    modules = bmeta.get('modules')
    modules_url = (
        urllib.parse.urljoin(storage, '/'.join([url_px, modules]))
        if modules else None
    )
    rootfs = plan_config.rootfs
    defconfig_full = bmeta['defconfig_full']
    defconfig = ''.join(defconfig_full.split('+')[:1])
    endian = 'big' if 'BIG_ENDIAN' in defconfig_full else 'little'
    describe = bmeta['git_describe']

    params = {
        'name': job_name,
        'dtb_url': dtb_url,
        'dtb_short': dtb,
        'dtb_full': dtb_full,
        'mach': target.mach,
        'kernel_url': kernel_url,
        'image_type': 'kernel-ci',
        'image_url': base_url,
        'modules_url': modules_url,
        'plan': plan_config.base_name,
        'plan_variant': plan_config.name,
        'kernel': describe,
        'tree': bmeta['job'],
        'defconfig': defconfig,
        'defconfig_full': defconfig_full,
        'fastboot': str(target.get_flag('fastboot')).lower(),
        'device_type': target.name,
        'base_device_type': target.base_name,
        'base_url': base_url,
        'endian': endian,
        'arch': arch,
        'git_branch': bmeta['git_branch'],
        'git_commit': bmeta['git_commit'],
        'git_describe': describe,
        'git_url': bmeta['git_url'],
        'initrd_url': rootfs.get_url('ramdisk', arch, endian),
        'kernel_image': kernel_img,
        'nfsrootfs_url': rootfs.get_url('nfs', arch, endian),
        'context': target.context,
        'rootfs_prompt': rootfs.prompt,
        'file_server_resource': file_server_resource,
        'build_environment': bmeta['build_environment'],
    }

    params.update(plan_config.params)
    params.update(target.params)

    return params
