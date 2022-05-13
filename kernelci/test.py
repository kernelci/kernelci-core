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

COMPRESSION_FORMATS = ['gz', 'bz2', 'xz']


def match_configs(configs, meta, lab):
    """Filter the test configs for a given kernel build and lab.

    *configs* is a list of all the initial test configs
    *meta* is a MetaStep object
    *dtbs* is the list of dtb files included in the kernel build
    *lab* is a Lab object instance

    The returned value is a list with a subset of the configs that match the
    provided kernel build meta-data and lab filters.
    """
    dtbs = meta.get_single_artifact('dtbs', attr='contents')
    bmeta = meta.get('bmeta')
    env, kernel, rev = (bmeta.get(key) for key in [
        'environment', 'kernel', 'revision'
    ])
    defconfig = kernel['defconfig_full']
    arch = env['arch']

    filters = {
        'arch': arch,
        'defconfig': defconfig,
        'kernel': rev['describe'],
        'build_environment': env['name'],
        'tree': rev['tree'],
        'branch': rev['branch'],
        'lab': lab.name,
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
        if dtb and (not dtbs or dtb not in dtbs):
            continue
        for plan_name, plan in test_config.test_plans.items():
            if not plan.match(filters):
                continue
            filters['plan'] = plan_name
            if lab.match(filters):
                match.add((test_config.device_type, plan))

    return match


def get_params(meta, target, plan_config, storage, device_ids):
    """Get a dictionary with all the test parameters to run a test job

    *meta* is a MetaStep object
    *target* is the name of the target platform to run the test
    *plan_config* is a TestPlan object for the test plan to run
    *storage* is the URL of the storage server
    *device_ids* iterable of device ids to run the test
    """

    def _get_compression(url):
        fmt = os.path.splitext(url)[1].replace('.', '') if url else ''
        return fmt if fmt in COMPRESSION_FORMATS else ''

    kernel, rev = (meta.get('bmeta', key) for key in ['kernel', 'revision'])
    arch = target.arch
    dtb = dtb_full = target.dtb
    if dtb:
        dtb_dir = meta.get_single_artifact('dtbs', attr='path')
        if dtb_dir:
            dtb = dtb_full = os.path.join(dtb_dir, target.dtb)
            dtb = os.path.basename(dtb)  # hack for dtbs in subfolders
    publish_path = kernel['publish_path']
    job_px = publish_path.replace('/', '-')
    url_px = publish_path
    job_name = '-'.join([job_px, dtb or 'no-dtb',
                         target.name, plan_config.name])
    base_url = urllib.parse.urljoin(storage, '/'.join([url_px, '']))
    kernel_img = meta.get_single_artifact('kernel', 'image', 'path')
    kernel_url = urllib.parse.urljoin(storage, '/'.join([url_px, kernel_img]))
    if dtb_full and dtb_full.endswith('.dtb'):
        dtb_url = urllib.parse.urljoin(
            storage, '/'.join([url_px, dtb_full]))
    else:
        dtb_url = None
    modules = meta.get_single_artifact('modules', attr='path')
    modules_url = (
        urllib.parse.urljoin(storage, '/'.join([url_px, modules]))
        if modules else None
    )
    modules_compression = _get_compression(modules_url)
    defconfig_full = kernel['defconfig_full']
    defconfig = ''.join(defconfig_full.split('+')[:1])
    endian = kernel["endianness"]
    describe = rev['describe']
    kselftests = meta.get_single_artifact('kselftest', attr='path')
    kselftests_url = (
        urllib.parse.urljoin(storage, '/'.join([url_px, kselftests]))
        if kselftests else None
    )

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
        'modules_compression': modules_compression,
        'plan': plan_config.base_name,
        'plan_variant': plan_config.name,
        'kernel': describe,
        'tree': rev['tree'],
        'defconfig': defconfig,
        'defconfig_full': defconfig_full,
        'fastboot': str(target.get_flag('fastboot')).lower(),
        'device_type': target.name,
        'base_device_type': target.base_name,
        'base_url': base_url,
        'endian': endian,
        'arch': arch,
        'git_branch': rev['branch'],
        'git_commit': rev['commit'],
        'git_describe': describe,
        'git_url': rev['url'],
        'kernel_image': os.path.basename(kernel_img),
        'context': target.context,
        'file_server_resource': publish_path,
        'build_environment': meta.get('bmeta', 'environment', 'name'),
        'kselftests_url': kselftests_url,
    }

    rootfs = plan_config.rootfs
    if rootfs:
        initrd_url = rootfs.get_url('ramdisk', arch, endian)
        initrd_compression = _get_compression(initrd_url)
        nfsroot_url = rootfs.get_url('nfs', arch, endian)
        nfsroot_compression = _get_compression(nfsroot_url)
        params.update({
            'initrd_url': initrd_url,
            'initrd_compression': initrd_compression,
            'nfsrootfs_url': nfsroot_url,
            'nfsroot_compression': nfsroot_compression,
            'rootfs_prompt': rootfs.prompt,
        })
        params.update(rootfs.params)

    params.update(plan_config.params)
    params.update(target.params)
    params.update({'device_ids': device_ids})

    return params
