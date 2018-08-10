# Copyright (C) 2018 Collabora Limited
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


class YAMLObject(object):
    """Base class with helper methods to initialise objects from YAML data."""

    @classmethod
    def _kw_from_yaml(cls, data, args):
        """Create some keyword arguments based on a YAML dictionary

        Return a dictionary suitable to be used as Python keyword arguments in
        an object constructor using values from some YAML *data*.  The *args*
        is a list of keys to look up from the *data* and convert to a
        dictionary.  Keys that are not in the YAML data are simply omitted from
        the returned keywords, relying on default values in object
        constructors.
        """
        return {
            k: v for k, v in ((k, data.get(k)) for k in args) if v
        }


class Filter(object):
    """Base class to implement arbitrary configuration filters."""

    def __init__(self, items):
        """The *items* can be any data used to filter configurations."""
        self._items = items

    def match(self, **kw):
        """Return True if the given *kw* keywords match the filter."""
        raise NotImplementedError("Filter.match() is not implemented")


class Blacklist(Filter):
    """Blacklist filter to discard certain configurations.

    Blacklist *items* are a dictionary associating keys with lists of values.
    Any configuration with a key-value pair present in these lists will be
    rejected.
    """

    def match(self, **kw):
        for k, v in kw.iteritems():
            bl = self._items.get(k)
            if not bl:
                continue
            if any(x in v for x in bl):
                return False

        return True


class Whitelist(Filter):
    """Whitelist filter to only accept certain configurations.

    Whitelist *items* are a dictionary associating keys with lists of values.
    For a configuration to be accepted, there must be a value found in each of
    these lists.
    """

    def match(self, **kw):
        for k, wl in self._items.iteritems():
            v = kw.get(k)
            if not v:
                return False
            if not any(x in v for x in wl):
                return False

        return True


class Combination(Filter):
    """Combination filter to only accept some combined configurations.

    Combination *items* are a dictionary with 'keys' and 'values'.  The 'keys'
    are a list of keywords to look for, and 'values' are a list of combined
    values for the given keys.  The length of each 'values' item must therefore
    match the length of the 'keys' list, and the order of the values must match
    the order of the keys.
    """

    def __init__(self, items):
        self._keys = tuple(items['keys'])
        self._values = list(tuple(values) for values in items['values'])

    def match(self, **kw):
        filter_values = tuple(kw.get(k) for k in self._keys)
        return filter_values in self._values


class FilterFactory(YAMLObject):
    """Factory to create filters from YAML data."""

    _classes = {
        'blacklist': Blacklist,
        'whitelist': Whitelist,
        'combination': Combination,
    }

    @classmethod
    def from_yaml(cls, filter_params):
        """Iterate through the YAML filters and return Filter objects."""
        filter_list = []
        for f in filter_params:
            for filter_type, items in f.iteritems():
                filter_cls = cls._classes[filter_type]
                filter_list.append(filter_cls(items))
        return filter_list

    @classmethod
    def from_data(cls, data, default_filters=[]):
        """Look for filters in YAML *data* or return *default_filters*.

        Look for a *filters* element in the YAML *data* dictionary.  If there
        is one, iterate over each item to return a list of Filter objects.
        Otherwise, return *default_filters*.
        """
        params = data.get('filters')
        return cls.from_yaml(params) if params else default_filters


class DeviceType(YAMLObject):
    """Device type model."""

    def __init__(self, name, mach, arch, boot_method, dtb=None,
                 flags=[], filters=[], context={}):
        """A device type describes a category of equivalent hardware devices.

        *name* is unique for the device type, typically as used by LAVA.
        *mach* is the name of the SoC manufacturer.
        *arch* is the CPU architecture following the Linux kernel convention.
        *boot_method* is the name of the boot method to use.
        *dtb* is an optional name for a device tree binary.
        *flags* is a list of optional arbitrary strings.
        *filters* is a list of Filter objects associated with this device type.
        *context* is an arbirary dictionary used when scheduling tests.
        """
        self._name = name
        self._mach = mach
        self._arch = arch
        self._boot_method = boot_method
        self._dtb = dtb
        self._flags = flags
        self._filters = filters
        self._context = context

    def __repr__(self):
        return self.name

    @property
    def name(self):
        return self._name

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
    def context(self):
        return self._context

    def get_flag(self, name):
        return name in self._flags

    def match(self, flags, config):
        """Checks if the given *flags* and *config* match this device type."""
        return (
            all(not v or self.get_flag(k) for k, v in flags.iteritems()) and
            all(f.match(**config) for f in self._filters)
        )


class DeviceType_arm(DeviceType):

    def __init__(self, name, mach, arch='arm', *args, **kw):
        """arm device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super(DeviceType_arm, self).__init__(name, mach, arch, *args, **kw)


class DeviceType_arm64(DeviceType):

    def __init__(self, name, mach, arch='arm64', *args, **kw):
        """arm64 device type with a device tree."""
        kw.setdefault('dtb', '{}/{}.dtb'.format(mach, name))
        super(DeviceType_arm64, self).__init__(name, mach, arch, *args, **kw)


class DeviceTypeFactory(YAMLObject):
    """Factory to create device types from YAML data."""

    _classes = {
        'arm-dtb': DeviceType_arm,
        'arm64-dtb': DeviceType_arm64,
    }

    @classmethod
    def from_yaml(cls, name, device_type, default_filters=[]):
        kw = cls._kw_from_yaml(device_type, [
            'mach', 'arch', 'boot_method', 'dtb', 'flags', 'context'])
        kw.update({
            'name': device_type.get('name', name),
            'filters': FilterFactory.from_data(device_type, default_filters),
        })
        cls_name = device_type.get('class')
        device_cls = cls._classes[cls_name] if cls_name else DeviceType
        return device_cls(**kw)


class RootFS(YAMLObject):
    """Root file system model."""

    _arch_dict = {}

    def __init__(self, url_formats, boot_protocol='tftp', root_type=None,
                 prompt="/ #"):
        """A root file system is any user-space that can be used in test jobs.

        *url_formats* are a dictionary with a format string for each type of
                      file system available (ramdisk, nfs...).  There is
                      typically only one entry here for the main *root_type*,
                      but multiple entries are possible in particular to boot
                      with first a ramdisk and then pivot to nfs root.

        *boot_protocol* is how the file system is made available to the kernel,
                        by default `tftp` typically to download a ramdisk.

        *root_type* is the name of the file system type (ramdisk, ...) as used
                    in the job template naming scheme.

        *prompt* is a string used in the job definition to tell when the
                 user-space is available to run some commands.
        """
        self._url_format = url_formats
        self._root_type = root_type or url_formats.keys()[0]
        self._boot_protocol = boot_protocol
        self._prompt = prompt

    @classmethod
    def from_yaml(cls, file_system_types, rootfs):
        kw = cls._kw_from_yaml(rootfs, [
            'boot_protocol', 'root_type', 'prompt'])
        fstype = file_system_types[rootfs['type']]
        base_url = fstype['url']
        kw['url_formats'] = {
            fs: '/'.join([base_url, url]) for fs, url in (
                (fs, rootfs.get(fs)) for fs in ['ramdisk', 'nfs'])
            if url
        }
        obj = cls(**kw)
        arch_map = fstype.get('arch_map')
        if arch_map:
            obj._arch_dict = {
                tuple(v.values()): k for k, v in arch_map.iteritems()
            }
        return obj

    @property
    def prompt(self):
        return self._prompt

    @property
    def boot_protocol(self):
        return self._boot_protocol

    @property
    def root_type(self):
        return self._root_type

    def get_url(self, fs_type, arch, endianness):
        """Get the URL of the file system for the given variant and arch.

        The *fs_type* should match one of the URL patterns known to this root
        file system.
        """
        fmt = self._url_format.get(fs_type)
        if not fmt:
            return None
        arch_name = self._arch_dict.get((arch, endianness))
        if not arch_name:
            arch_name = self._arch_dict.get((arch,), arch)
        return fmt.format(arch=arch_name)


class TestPlan(YAMLObject):
    """Test plan model."""

    _pattern = '{plan}/{category}-{method}-{protocol}-{rootfs}-{plan}-template.jinja2'

    def __init__(self, name, rootfs, category='generic', filters=[],
                 pattern=None):
        """A test plan is an arbitrary group of test cases to be run.

        *name* is the overall arbitrary test plan name, used when looking for
               job template files.

        *rootfs* is a RootFS object to be used to run this test plan.

        *category* is to classify the type of job to be run, used when looking
                   for job template files.

        *filters* is a list of Filter objects associated with this test plan.

        *pattern* is a string pattern to create the path to the job template
                  file, see TestPlan._pattern for the default value with the
                  regular template file naming scheme.
        """
        self._name = name
        self._rootfs = rootfs
        self._category = category
        self._filters = filters
        if pattern:
            self._pattern = pattern

    @classmethod
    def from_yaml(cls, name, test_plan, file_systems, default_filters=[]):
        kw = {
            'name': name,
            'rootfs': file_systems[test_plan['rootfs']],
            'filters': FilterFactory.from_data(test_plan, default_filters),
        }
        kw.update(cls._kw_from_yaml(test_plan, ['name', 'category', 'pattern']))
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def rootfs(self):
        return self._rootfs

    def get_template_path(self, boot_method):
        """Get the path to the template file for the given *boot_method*

        As different device types use different boot methods (u-boot, grub...),
        each test plan can have several template variants to accomodate for
        these.  All the other parameters are attributes of the test plan.
        """
        return self._pattern.format(
            category=self._category,
            method=boot_method,
            protocol=self.rootfs.boot_protocol,
            rootfs=self.rootfs.root_type,
            plan=self.name)

    def match(self, config):
        return all(f.match(**config) for f in self._filters)


class TestConfig(YAMLObject):
    """Test configuration model."""

    def __init__(self, device_type, test_plans, filters=[]):
        """A test configuration has a *device_type* and a list of *test_plans*.

        *device_type* is a DeviceType object.
        *test_plans* is a list of TestPlan objects to run on the device type.
        """
        self._device_type = device_type
        self._test_plans = {
            t.name: t for t in test_plans
        }
        self._filters = filters

    @classmethod
    def from_yaml(cls, test_config, device_types, test_plans,
                  default_filters=[]):
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

    def match(self, arch, plan, flags, config):
        return (
            plan in self._test_plans and
            self._test_plans[plan].match(config) and
            self.device_type.arch == arch and
            self.device_type.match(flags, config) and
            all(f.match(**config) for f in self._filters)
        )

    def get_template_path(self, plan):
        test_plan = self._test_plans[plan]
        return test_plan.get_template_path(self._device_type.boot_method)


def load_from_yaml(yaml_path="test-configs.yaml"):
    with open(yaml_path) as f:
        data = yaml.load(f)

    fs_types = data['file_system_types']

    file_systems = {
        name: RootFS.from_yaml(fs_types, rootfs)
        for name, rootfs in data['file_systems'].iteritems()
    }

    plan_filters = FilterFactory.from_yaml(data['test_plan_default_filters'])

    test_plans = {
        name: TestPlan.from_yaml(name, test_plan, file_systems, plan_filters)
        for name, test_plan in data['test_plans'].iteritems()
    }

    device_filters = FilterFactory.from_yaml(data['device_default_filters'])

    device_types = {
        name: DeviceTypeFactory.from_yaml(name, device_type, device_filters)
        for name, device_type in data['device_types'].iteritems()
    }

    test_configs = [
        TestConfig.from_yaml(test_config, device_types, test_plans)
        for test_config in data['test_configs']
    ]

    data = {
        'file_systems': file_systems,
        'test_plans': test_plans,
        'device_types': device_types,
        'test_configs': test_configs,
    }

    return data
