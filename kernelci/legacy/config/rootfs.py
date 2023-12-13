# Copyright (C) 2019 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
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

import sys
import yaml

from kernelci import sort_check
from .base import _YAMLObject


class RootFS(_YAMLObject):
    def __init__(self, name, rootfs_type):
        self._name = name
        self._rootfs_type = rootfs_type

    @property
    def name(self):
        return self._name

    @property
    def rootfs_type(self):
        return self._rootfs_type

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'rootfs_type'})
        return attrs


class RootFS_Debos(RootFS):
    def __init__(self, name, rootfs_type, debian_release=None,
                 arch_list=None, extra_packages=None, extra_firmware=None,
                 linux_fw_version="",
                 extra_packages_remove=None,
                 extra_files_remove=None, script="",
                 test_overlay="", crush_image_options=None, debian_mirror="",
                 keyring_package="", keyring_file="", debos_memory="",
                 debos_cpus="", debos_scratchsize="", imagesize=""):
        super().__init__(name, rootfs_type)
        self._debian_release = debian_release
        self._arch_list = arch_list or list()
        self._extra_packages = extra_packages or list()
        self._extra_packages_remove = extra_packages_remove or list()
        self._extra_firmware = extra_firmware or list()
        self._linux_fw_version = linux_fw_version
        self._extra_files_remove = extra_files_remove or list()
        self._script = script
        self._test_overlay = test_overlay
        self._crush_image_options = crush_image_options or list()
        self._debian_mirror = debian_mirror
        self._keyring_package = keyring_package
        self._keyring_file = keyring_file
        self._imagesize = imagesize
        self._debos_memory = debos_memory
        self._debos_cpus = debos_cpus
        self._debos_scratchsize = debos_scratchsize

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        # ToDo: use a single RootFS class and move specific options to a
        # "params" dictionary in YAML
        kw.update(cls._kw_from_yaml(config, [
            'rootfs_type',
            'debian_release',
            'arch_list',
            'debian_mirror',
            'keyring_package',
            'keyring_file',
            'imagesize',
            'extra_packages',
            'extra_packages_remove',
            'extra_files_remove',
            'extra_firmware',
            'linux_fw_version',
            'script',
            'test_overlay',
            'crush_image_options',
            'debos_memory',
            'debos_cpus',
            'debos_scratchsize',
        ]))
        return cls(**kw)

    @property
    def debian_release(self):
        return self._debian_release

    @property
    def arch_list(self):
        return list(self._arch_list)

    @property
    def extra_packages(self):
        return list(self._extra_packages)

    @property
    def extra_packages_remove(self):
        return list(self._extra_packages_remove)

    @property
    def extra_files_remove(self):
        return list(self._extra_files_remove)

    @property
    def extra_firmware(self):
        return list(self._extra_firmware)

    @property
    def linux_fw_version(self):
        return self._linux_fw_version

    @property
    def script(self):
        return self._script

    @property
    def test_overlay(self):
        return self._test_overlay

    @property
    def crush_image_options(self):
        return list(self._crush_image_options)

    @property
    def debian_mirror(self):
        return self._debian_mirror

    @property
    def keyring_package(self):
        return self._keyring_package

    @property
    def keyring_file(self):
        return self._keyring_file

    @property
    def imagesize(self):
        return self._imagesize

    @property
    def debos_memory(self):
        return self._debos_memory

    @property
    def debos_cpus(self):
        return self._debos_cpus

    @property
    def debos_scratchsize(self):
        return self._debos_scratchsize

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({
            'debian_release',
            'arch_list',
            'debian_mirror',
            'keyring_package',
            'keyring_file',
            'imagesize',
            'extra_packages',
            'extra_packages_remove',
            'extra_files_remove',
            'extra_firmware',
            'linux_fw_version',
            'script',
            'test_overlay',
            'crush_image_options',
            'debos_memory',
            'debos_cpus',
            'debos_scratchsize',
        })
        return attrs


class RootFS_Buildroot(RootFS):
    def __init__(self, name, rootfs_type, git_url, git_branch,
                 arch_list=None, frags=None):
        super().__init__(name, rootfs_type)
        self._git_url = git_url
        self._git_branch = git_branch
        self._arch_list = arch_list or list()
        self._frags = frags or list()
        self._attrs = set()

    @property
    def git_url(self):
        return self._git_url

    @property
    def git_branch(self):
        return self._git_branch

    @property
    def frags(self):
        return self._frags

    @property
    def arch_list(self):
        return list(self._arch_list)

    def _set_attrs(self, attrs):
        self._attrs = set(attrs)

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({
            'arch_list',
            'git_url',
            'git_branch',
            'frags',
        })
        return attrs


class RootFS_ChromiumOS(RootFS):
    def __init__(self, name, rootfs_type, arch_list=None, board=None,
                 branch=None, serial=None):
        super().__init__(name, rootfs_type)
        self._arch_list = arch_list or list()
        self._board = board
        self._branch = branch
        self._serial = serial

    @property
    def arch_list(self):
        return list(self._arch_list)

    @property
    def board(self):
        return self._board

    @property
    def branch(self):
        return self._branch

    @property
    def serial(self):
        return self._serial

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({
            'arch_list',
            'board',
            'branch',
            'serial',
        })
        return attrs


class RootFSFactory(_YAMLObject):
    _rootfs_types = {
        'debos': RootFS_Debos,
        'buildroot': RootFS_Buildroot,
        'chromiumos': RootFS_ChromiumOS,
    }

    @classmethod
    def from_yaml(cls, name, rootfs):
        rootfs_type = rootfs.get('rootfs_type')
        if rootfs_type is None:
            raise TypeError("rootfs_type cannot be Empty")

        rootfs_cls = cls._rootfs_types.get(rootfs_type)
        if rootfs_cls is None:
            raise ValueError("Unsupported value {}".format(rootfs_type))

        return rootfs_cls.from_yaml(rootfs, name=name)


def from_yaml(data, filters):
    rootfs_configs = {
        name: RootFSFactory.from_yaml(name, rootfs)
        for name, rootfs in data.get('rootfs_configs', {}).items()
    }

    return {
        'rootfs_configs': rootfs_configs,
    }


def validate(configs):
    """Validate rootfs config

        *configs* contains rootfs-configs.yaml entries
    """
    err = sort_check(configs['rootfs_configs'])
    if err:
        print("Rootfs broken order: '{}' before '{}".format(*err))
        return False
    for name, config in configs['rootfs_configs'].items():
        if config.rootfs_type == 'debos':
            return _validate_debos(name, config)
        elif config.rootfs_type == 'buildroot':
            return _validate_buildroot(name, config)
        elif config.rootfs_type == 'chromiumos':
            return _validate_chromiumos(name, config)
        else:
            print('Invalid rootfs type {} for config name {}'
                  .format(config.rootfs_type, name))
            return False


def _validate_debos(name, config):
    err = sort_check(config.arch_list)
    if err:
        print("Arch order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    err = sort_check(config.extra_packages)
    if err:
        print("Packages order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    err = sort_check(config.extra_packages_remove)
    if err:
        print("Packages order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    return True


def _validate_buildroot(name, config):
    err = sort_check(config.arch_list)
    if err:
        print("Arch order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    err = sort_check(config.frags)
    if err:
        print("Frags order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    return True


def _validate_chromiumos(name, config):
    err = sort_check(config.arch_list)
    if err:
        print("Arch order broken for {}: '{}' before '{}".format(
            name, err[0], err[1]))
        return False
    return True


def dump_configs(configs):
    """Prints rootfs configs to stdout

        *configs* contains rootfs-configs.yaml entries
    """
    for config_name, config in configs['rootfs_configs'].items():
        if config.rootfs_type == 'debos':
            _dump_config_debos(config_name, config)
        elif config.rootfs_type == 'buildroot':
            _dump_config_buildroot(config_name, config)
        elif config.rootfs_type == 'chromiumos':
            _dump_config_chromiumos(config_name, config)


def _dump_config_debos(config_name, config):
    print(config_name)
    print('\trootfs_type: {}'.format(config.rootfs_type))
    print('\tarch_list: {}'.format(config.arch_list))
    print('\tdebian_release: {}'.format(config.debian_release))
    print('\textra_packages: {}'.format(config.extra_packages))
    print('\textra_packages_remove: {}'.format(
        config.extra_packages_remove))
    print('\textra_files_remove: {}'.format(
        config.extra_files_remove))
    print('\textra_firmware: {}'.format(config.extra_firmware))
    print('\tlinux_fw_version: {}'.format(config.linux_fw_version))
    print('\tscript: {}'.format(config.script))
    print('\ttest_overlay: {}'.format(config.test_overlay))
    print('\tcrush_image_options: {}'.format(
        config.crush_image_options))
    print('\tdebian_mirror: {}'.format(config.debian_mirror))
    print('\tkeyring_package: {}'.format(config.keyring_package))
    print('\tkeyring_file: {}'.format(config.keyring_file))
    print('\timagesize: {}'.format(config.imagesize))
    print('\tdebos_memory: {}'.format(config.debos_memory))
    print('\tdebos_cpu: {}'.format(config.debos_cpu))
    print('\tdebos_scratchsize: {}'.format(config.debos_scratchsize))


def _dump_config_buildroot(config_name, config):
    print(config_name)
    print('\trootfs_type: {}'.format(config.rootfs_type))
    print('\tarch_list: {}'.format(config.arch_list))
    print('\tfrags: {}'.format(config.frags))


def _dump_config_chromiumos(config_name, config):
    print(config_name)
    print('\trootfs_type: {}'.format(config.rootfs_type))
    print('\tarch_list: {}'.format(config.arch_list))
    print('\board: {}'.format(config.board))
    print('\branch: {}'.format(config.branch))
    print('\tserial: {}'.format(config.serial))
