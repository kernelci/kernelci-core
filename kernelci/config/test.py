# Copyright (C) 2018, 2019 Collabora Limited
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

import yaml

from kernelci.config.base import FilterFactory, YAMLObject


class DeviceType(YAMLObject):
    """Device type model."""

    def __init__(self, name, mach, arch, boot_method, dtb=None, base_name=None,
                 flags=None, filters=None, context=None, params=None):
        """A device type describes a category of equivalent hardware devices.

        *name* is unique for the device type, typically as used by LAVA.
        *mach* is the name of the SoC manufacturer.
        *arch* is the CPU architecture following the Linux kernel convention.
        *boot_method* is the name of the boot method to use.
        *dtb* is an optional name for a device tree binary.
        *base_name* is the name of the base device type used in test labs.
        *flags* is a list of optional arbitrary strings.
        *filters* is a list of Filter objects associated with this device type.
        *context* is an arbirary dictionary used when scheduling tests.
        *params* is a dictionary with parameters to pass to the test job
                 generator.
        """
        self._name = name
        self._mach = mach
        self._arch = arch
        self._boot_method = boot_method
        self._dtb = dtb
        self._base_name = base_name or name
        self._params = params or dict()
        self._flags = flags or list()
        self._filters = filters or list()
        self._context = context or dict()

    def __repr__(self):
        return self.name

    @property
    def name(self):
        return self._name

    @property
    def base_name(self):
        return self._base_name

    @property
    def mach(self):
        return self._mach

    @property
    def arch(self):
        return self._arch

    @property
    def boot_method(self):
        return self._boot_method

    @property
    def dtb(self):
        return self._dtb

    @property
    def params(self):
        return dict(self._params)

    @property
    def context(self):
        return self._context

    def get_flag(self, name):
        return name in self._flags

    def match(self, flags, config):
        """Checks if the given *flags* and *config* match this device type."""
        return (
            all(not v or self.get_flag(k) for k, v in flags.items()) and
            all(f.match(**config) for f in self._filters)
        )


class DeviceType_arc(DeviceType):

    def __init__(self, name, mach, arch='arc', *args, **kw):
        """arc device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super().__init__(name, mach, arch, *args, **kw)


class DeviceType_arm(DeviceType):

    def __init__(self, name, mach, arch='arm', *args, **kw):
        """arm device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super().__init__(name, mach, arch, *args, **kw)


class DeviceType_mips(DeviceType):

    def __init__(self, name, mach, arch='mips', *args, **kw):
        """mips device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super().__init__(name, mach, arch, *args, **kw)


class DeviceType_arm64(DeviceType):

    def __init__(self, name, mach, arch='arm64', *args, **kw):
        """arm64 device type with a device tree."""
        kw.setdefault('dtb', '{}/{}.dtb'.format(mach, name))
        super().__init__(name, mach, arch, *args, **kw)


class DeviceType_riscv(DeviceType):

    def __init__(self, name, mach, arch='riscv', *args, **kw):
        """RISCV device type with a device tree."""
        kw.setdefault('dtb', '{}/{}.dtb'.format(mach, name))
        super().__init__(name, mach, arch, *args, **kw)


class DeviceTypeFactory(YAMLObject):
    """Factory to create device types from YAML data."""

    _classes = {
        'arc-dtb': DeviceType_arc,
        'mips-dtb': DeviceType_mips,
        'arm-dtb': DeviceType_arm,
        'arm64-dtb': DeviceType_arm64,
        'riscv-dtb': DeviceType_riscv,
    }

    @classmethod
    def from_yaml(cls, name, device_type, default_filters=None):
        kw = {
            'name': name,
            'base_name': device_type.get('base_name'),
            'filters': FilterFactory.from_data(device_type, default_filters),
        }
        kw.update(cls._kw_from_yaml(device_type, [
            'mach', 'arch', 'boot_method',
            'dtb', 'flags', 'context', 'params',
        ]))
        cls_name = device_type.get('class')
        device_cls = cls._classes[cls_name] if cls_name else DeviceType
        return device_cls(**kw)


class RootFSType(YAMLObject):
    """Root file system type model."""

    def __init__(self, url, arch_dict=None):
        """A root file system type covers common file system features.

        *url* is the base URL for file system binaries.  Each file system
              variant will have some URLs based on this one with various
              formats and architectures.

        *arch_dict* is a dictionary to map CPU architecture names following the
                    kernel convention with distribution architecture names as
                    used by the file system type.  Keys are the names used by
                    the root file system type (distro), and values are lists of
                    dictionaries with kernel architecture names and other
                    properties such as the endinanness.
        """
        self._url = url
        self._arch_dict = arch_dict or dict()

    @classmethod
    def from_yaml(cls, fs_type):
        kw = cls._kw_from_yaml(fs_type, ['url'])
        arch_map = fs_type.get('arch_map')
        if arch_map:
            arch_dict = {}
            for arch_name, arch_dicts in arch_map.items():
                for d in arch_dicts:
                    key = tuple((k, v) for (k, v) in d.items())
                    arch_dict[key] = arch_name
            kw['arch_dict'] = arch_dict
        return cls(**kw)

    @property
    def url(self):
        return self._url

    def get_arch_name(self, arch, endian):
        arch_key = ('arch', arch)
        endian_key = ('endian', endian)
        arch_name = (self._arch_dict.get((arch_key, endian_key)) or
                     self._arch_dict.get((arch_key,), arch))
        return arch_name


class RootFS(YAMLObject):
    """Root file system model."""

    def __init__(self, url_formats, fs_type, boot_protocol='tftp',
                 root_type=None, prompt="/ #", params=None):
        """A root file system is any user-space that can be used in test jobs.

        *url_formats* are a dictionary with a format string for each type of
                      file system available (ramdisk, nfs...).  There is
                      typically only one entry here for the main *root_type*,
                      but multiple entries are possible in particular to boot
                      with first a ramdisk and then pivot to nfs root.

        *fs_type* is a RootFSType instance.

        *boot_protocol* is how the file system is made available to the kernel,
                        by default `tftp` typically to download a ramdisk.

        *root_type* is the name of the file system type (ramdisk, ...) as used
                    in the job template naming scheme.

        *prompt* is a string used in the job definition to tell when the
                 user-space is available to run some commands.

        *params" is a dictionary with parameters to pass to the test job
                 generator.
        """
        self._url_format = url_formats
        self._fs_type = fs_type
        self._root_type = root_type or list(url_formats.keys())[0]
        self._boot_protocol = boot_protocol
        self._prompt = prompt
        self._params = params or dict()
        self._arch_dict = {}

    @classmethod
    def from_yaml(cls, file_system_types, rootfs):
        kw = cls._kw_from_yaml(rootfs, [
            'boot_protocol', 'root_type', 'prompt', 'params'])
        fs_type = file_system_types[rootfs['type']]
        base_url = fs_type.url
        kw['fs_type'] = fs_type
        kw['url_formats'] = {
            fs: '/'.join([base_url, url]) for fs, url in (
                (fs, rootfs.get(fs)) for fs in ['ramdisk', 'nfs'])
            if url
        }
        return cls(**kw)

    @property
    def prompt(self):
        return self._prompt

    @property
    def boot_protocol(self):
        return self._boot_protocol

    @property
    def root_type(self):
        return self._root_type

    @property
    def params(self):
        return dict(self._params)

    def get_url(self, fs_type, arch, endian):
        """Get the URL of the file system for the given variant and arch.

        The *fs_type* should match one of the URL patterns known to this root
        file system.
        """
        fmt = self._url_format.get(fs_type)
        if not fmt:
            return None
        arch_name = self._fs_type.get_arch_name(arch, endian)
        return fmt.format(arch=arch_name)


class TestPlan(YAMLObject):
    """Test plan model."""

    _pattern = \
        '{plan}/{category}-{method}-{protocol}-{rootfs}-{plan}-template.jinja2'

    def __init__(self, name, rootfs, base_name=None, params=None,
                 category='generic', filters=None, pattern=None):
        """A test plan is an arbitrary group of test cases to be run.

        *name* is the overall arbitrary test plan name, used when looking for
               job template files.

        *rootfs* is a RootFS object to be used to run this test plan.

        *base_name* is the name of the base test plan which this test plan
                    configuration refers to.

        *params" is a dictionary with parameters to pass to the test job
                 generator.

        *category* is to classify the type of job to be run, used when looking
                   for job template files.

        *filters* is a list of Filter objects associated with this test plan.

        *pattern* is a string pattern to create the path to the job template
                  file, see TestPlan._pattern for the default value with the
                  regular template file naming scheme.

        """
        self._name = name
        self._rootfs = rootfs
        self._base_name = base_name or name
        self._params = params or dict()
        self._category = category
        self._filters = filters or list()
        if pattern:
            self._pattern = pattern

    @classmethod
    def from_yaml(cls, name, test_plan, file_systems, default_filters=None):
        rootfs_name = test_plan.get('rootfs')
        kw = {
            'name': name,
            'rootfs': file_systems[rootfs_name] if rootfs_name else None,
            'base_name': test_plan.get('base_name'),
            'filters': FilterFactory.from_data(test_plan, default_filters),
        }
        kw.update(cls._kw_from_yaml(test_plan, [
            'name', 'category', 'pattern', 'params']))
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def rootfs(self):
        return self._rootfs

    @property
    def base_name(self):
        return self._base_name

    @property
    def params(self):
        return dict(self._params)

    def get_template_path(self, boot_method):
        """Get the path to the template file for the given *boot_method*

        As different device types use different boot methods (u-boot, grub...),
        each test plan can have several template variants to accomodate for
        these.  All the other parameters are attributes of the test plan.
        """
        return self._pattern.format(
            category=self._category,
            method=boot_method,
            protocol=self.rootfs.boot_protocol if self.rootfs else None,
            rootfs=self.rootfs.root_type if self.rootfs else None,
            plan=self.name)

    def match(self, config):
        return all(f.match(**config) for f in self._filters)


class TestConfig(YAMLObject):
    """Test configuration model."""

    def __init__(self, device_type, test_plans, filters=None):
        """A test configuration has a *device_type* and a list of *test_plans*.

        *device_type* is a DeviceType object.
        *test_plans* is a list of TestPlan objects to run on the device type.
        """
        self._device_type = device_type
        self._test_plans = {
            t.name: t for t in test_plans
        }
        self._filters = filters or list()

    @classmethod
    def from_yaml(cls, test_config, device_types, test_plans,
                  default_filters=None):
        kw = {
            'device_type': device_types[test_config['device_type']],
            'test_plans': [test_plans[test]
                           for test in test_config['test_plans']],
            'filters': FilterFactory.from_data(test_config, default_filters),
        }

        return cls(**kw)

    @property
    def device_type(self):
        return self._device_type

    @property
    def test_plans(self):
        return self._test_plans

    def match(self, arch, flags, config, plan=None):
        return (
            (plan is None or (
                plan in self._test_plans and
                self._test_plans[plan].match(config)
            )) and
            (self.device_type.arch is None or (
                self.device_type.arch == arch
            )) and
            self.device_type.match(flags, config) and
            all(f.match(**config) for f in self._filters)
        )

    def get_template_path(self, plan):
        test_plan = self._test_plans[plan]
        return test_plan.get_template_path(self._device_type.boot_method)


def from_yaml(data):
    fs_types = {
        name: RootFSType.from_yaml(fs_type)
        for name, fs_type in data.get('file_system_types', {}).items()
    }

    file_systems = {
        name: RootFS.from_yaml(fs_types, rootfs)
        for name, rootfs in data.get('file_systems', {}).items()
    }

    plan_filters = FilterFactory.from_yaml(
        data.get('test_plan_default_filters', {})
    )

    test_plans = {
        name: TestPlan.from_yaml(name, test_plan, file_systems, plan_filters)
        for name, test_plan in data.get('test_plans', {}).items()
    }

    device_filters = FilterFactory.from_yaml(
        data.get('device_default_filters', {})
    )

    device_types = {
        name: DeviceTypeFactory.from_yaml(name, device_type, device_filters)
        for name, device_type in data.get('device_types', {}).items()
    }

    test_configs = [
        TestConfig.from_yaml(test_config, device_types, test_plans)
        for test_config in data.get('test_configs', [])
    ]

    return {
        'file_systems': file_systems,
        'test_plans': test_plans,
        'device_types': device_types,
        'test_configs': test_configs,
    }
