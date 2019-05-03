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


# -----------------------------------------------------------------------------
# Common classes for all config types
#

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
        } if data else dict()


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
    def from_data(cls, data, default_filters=None):
        """Look for filters in YAML *data* or return *default_filters*.

        Look for a *filters* element in the YAML *data* dictionary.  If there
        is one, iterate over each item to return a list of Filter objects.
        Otherwise, return *default_filters*.
        """
        params = data.get('filters')
        return cls.from_yaml(params) if params else default_filters


# -----------------------------------------------------------------------------
# Build configs
#

class Tree(YAMLObject):
    """Kernel git tree model."""

    def __init__(self, name, url):
        """A kernel git tree is essentially a repository with kernel branches.

        *name* is the name of the tree, such as "mainline" or "next".
        *url* is the git remote URL for the tree.
        """
        self._name = name
        self._url = url

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(config, ['url', 'name']))
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def url(self):
        return self._url


class Fragment(YAMLObject):
    """Kernel config fragment model."""

    def __init__(self, name, path, configs=None, defconfig=None):
        """A kernel config fragment is a list of config options in file.

        *name* is the name of the config fragment so it can be referred to in
               other configuration objects.

        *path* is the path where the config fragment either can be found,
               either from the git checkout or after being generated.

        *configs* is an optional list of kernel configs to use when generating
                  a config fragment that does not exist in the git checkout.

        *defconfig* is an optional defconfig name to use as a make target
                    instead of a real config path.  This is only used for
                    special cases such as the tiny.config fragment which needs
                    to be built with the tinyconfig make target.
        """
        self._name = name
        self._path = path
        self._configs = configs or list()
        self._defconfig = defconfig

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(config, [
            'name', 'path', 'configs', 'defconfig',
        ]))
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def configs(self):
        return list(self._configs)

    @property
    def defconfig(self):
        return self._defconfig


class Architecture(YAMLObject):
    """CPU architecture attributes."""

    def __init__(self, name, base_defconfig='defconfig', extra_configs=None,
                 fragments=None, filters=None):
        """Particularities to build kernels for each CPU architecture.

        *name* is the CPU architecture name as per the kernel's convention.

        *base_defconfig* is the defconfig used by default and as a basis when
                         adding fragments.

        *extra_configs* is a list of extra defconfigs and make targets to
                        build, for example allnoconfig, allmodconfig and any
                        arbitrary some_defconfig+CONFIG_XXX=y definitions.

        *fragments* is a list of CPU-specific config fragments to build if
                    present.

        *filters* is a list of filters to limit the number of builds, typically
                  using a list of defconfigs to blacklist or whitelist.
        """
        self._name = name
        self._base_defconfig = base_defconfig
        self._extra_configs = extra_configs or []
        self._fragments = fragments or []
        self._filters = filters or list()

    @classmethod
    def from_yaml(cls, data, name, fragments):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(data, [
            'name', 'base_defconfig', 'extra_configs',
        ]))
        cf = data.get('fragments')
        kw['fragments'] = [fragments[name] for name in cf] if cf else None
        kw['filters'] = FilterFactory.from_data(data)
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def base_defconfig(self):
        return self._base_defconfig

    @property
    def extra_configs(self):
        return list(self._extra_configs)

    @property
    def fragments(self):
        return list(self._fragments)

    def match(self, params):
        return all(f.match(**params) for f in self._filters)


class BuildEnvironment(YAMLObject):
    """Kernel build environment model."""

    def __init__(self, name, cc, cc_version, arch_map=None,
                 cross_compile=None):
        """A build environment is a compiler and tools to build a kernel.

        *name* is the name of the build environment so it can be referred to in
               other parts of the build configuration.  Typical build
               environment names include the compiler type and version such as
               "gcc-7" although this is entirely arbitrary.

        *cc* is the compiler type, such as "gcc" or "clang".  This is
            functional and indicates the actual compiler binary being used.

        *cc_version* is the full version of the compiler.

        *arch_map* is a dictionary mapping kernel CPU architecture names to
                   ones used in compiler names.  For example, gcc compilers are
                   the same "x86" for both "i386" and "x86_64" kernel
                   architectures.

        *cross_compile* is a dictionary mapping kernel CPU architecture names
                        to cross-compiler prefixes.
        """
        self._name = name
        self._cc = cc
        self._cc_version = str(cc_version)
        self._arch_map = arch_map or dict()
        self._cross_compile = cross_compile or dict()

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(
            config, ['name', 'cc', 'cc_version', 'arch_map', 'cross_compile']))
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def cc(self):
        return self._cc

    @property
    def cc_version(self):
        return self._cc_version

    def get_arch_name(self, kernel_arch):
        return self._arch_map.get(kernel_arch, kernel_arch)

    def get_cross_compile(self, kernel_arch):
        return self._cross_compile.get(kernel_arch, '')


class BuildVariant(YAMLObject):
    """A variant of a given build configuration."""

    def __init__(self, name, architectures, build_environment, fragments=None):
        """A build variant is a sub-section of a build configuration.

        *name* is the name of the build variant.  It is arbitrary and defined
               to be able to refer to the build variant in other parts of the
               build configurations or the code using it.

        *architectures* is a list of Architecture objects.  There can only be
                        one Architecture object for any given kernel CPU
                        architecture name.  This list defines the architectures
                        that should be built for a given build variant.

        *build_environment" is a BuildEnvironment object, to define which
                            compiler to use to build the kernels.

        *fragments* is an optional list of Fragment objects to define fragments
                    to build with this build variant.
        """
        self._name = name
        self._architectures = {arch.name: arch for arch in architectures}
        self._build_environment = build_environment
        self._fragments = fragments or list()

    @classmethod
    def from_yaml(cls, config, name, fragments, build_environments):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(
            config, ['name', 'build_environment', 'fragments']))
        kw['build_environment'] = build_environments[kw['build_environment']]
        kw['architectures'] = list(
            Architecture.from_yaml(data or {}, name, fragments)
            for name, data in config['architectures'].iteritems()
        )
        cf = kw.get('fragments')
        kw['fragments'] = [fragments[name] for name in cf] if cf else None
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def arch_list(self):
        return self._architectures.keys()

    @property
    def architectures(self):
        return list(self._architectures.values())

    def get_arch(self, arch_name):
        return self._architectures.get(arch_name)

    @property
    def build_environment(self):
        return self._build_environment

    @property
    def fragments(self):
        return list(self._fragments)


class BuildConfig(YAMLObject):
    """Build configuration model."""

    def __init__(self, name, tree, branch, variants):
        """A build configuration defines the actual kernels to be built.

        *name* is the name of the build configuration.  It is arbitrary and
               used in other places to refer to the build configuration.

        *tree* is a Tree object, where the kernel branche to be built can be
               found.

        *branch* is the name of the branch to build.  There can only be one
                 branch in each BuildConfig object.

        *variants* is a list of BuildVariant objects, to define all the
                   variants to build for this tree / branch combination.
        """
        self._name = name
        self._tree = tree
        self._branch = branch
        self._variants = variants

    @classmethod
    def from_yaml(cls, config, name, trees, fragments, build_envs, defaults):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(
            config, ['name', 'tree', 'branch']))
        kw['tree'] = trees[kw['tree']]
        config_variants = config.get('variants', defaults)
        variants = [
            BuildVariant.from_yaml(variant, name, fragments, build_envs)
            for name, variant in config_variants.iteritems()
        ]
        kw['variants'] = {v.name: v for v in variants}
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def tree(self):
        return self._tree

    @property
    def branch(self):
        return self._branch

    @property
    def variants(self):
        return list(self._variants.values())

    def get_variant(self, name):
        return self._variants[name]


# -----------------------------------------------------------------------------
# Test configs
#

class DeviceType(YAMLObject):
    """Device type model."""

    def __init__(self, name, mach, arch, boot_method, dtb=None,
                 flags=None, filters=None, context=None):
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
        self._flags = flags or list()
        self._filters = filters or list()
        self._context = context or dict()

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


class DeviceType_arc(DeviceType):

    def __init__(self, name, mach, arch='arc', *args, **kw):
        """arc device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super(DeviceType_arc, self).__init__(name, mach, arch, *args, **kw)


class DeviceType_arm(DeviceType):

    def __init__(self, name, mach, arch='arm', *args, **kw):
        """arm device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super(DeviceType_arm, self).__init__(name, mach, arch, *args, **kw)


class DeviceType_mips(DeviceType):

    def __init__(self, name, mach, arch='mips', *args, **kw):
        """mips device type with a device tree."""
        kw.setdefault('dtb', '{}.dtb'.format(name))
        super(DeviceType_mips, self).__init__(name, mach, arch, *args, **kw)


class DeviceType_arm64(DeviceType):

    def __init__(self, name, mach, arch='arm64', *args, **kw):
        """arm64 device type with a device tree."""
        kw.setdefault('dtb', '{}/{}.dtb'.format(mach, name))
        super(DeviceType_arm64, self).__init__(name, mach, arch, *args, **kw)


class DeviceTypeFactory(YAMLObject):
    """Factory to create device types from YAML data."""

    _classes = {
        'arc-dtb': DeviceType_arc,
        'mips-dtb': DeviceType_mips,
        'arm-dtb': DeviceType_arm,
        'arm64-dtb': DeviceType_arm64,
    }

    @classmethod
    def from_yaml(cls, name, device_type, default_filters=None):
        kw = cls._kw_from_yaml(device_type, [
            'mach', 'arch', 'boot_method', 'dtb', 'flags', 'context'])
        kw.update({
            'name': device_type.get('name', name),
            'filters': FilterFactory.from_data(device_type, default_filters),
        })
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
            for arch_name, arch_dicts in arch_map.iteritems():
                for d in arch_dicts:
                    key = tuple((k, v) for (k, v) in d.iteritems())
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
                 root_type=None, prompt="/ #"):
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
        """
        self._url_format = url_formats
        self._fs_type = fs_type
        self._root_type = root_type or url_formats.keys()[0]
        self._boot_protocol = boot_protocol
        self._prompt = prompt
        self._arch_dict = {}

    @classmethod
    def from_yaml(cls, file_system_types, rootfs):
        kw = cls._kw_from_yaml(rootfs, [
            'boot_protocol', 'root_type', 'prompt'])
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

    _pattern = '{plan}/{category}-{method}-{protocol}-{rootfs}-{plan}-template.jinja2'

    def __init__(self, name, rootfs, params=None, category='generic',
                 filters=None, pattern=None):
        """A test plan is an arbitrary group of test cases to be run.

        *name* is the overall arbitrary test plan name, used when looking for
               job template files.

        *rootfs* is a RootFS object to be used to run this test plan.

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
        self._params = params or dict()
        self._category = category
        self._filters = filters or list()
        if pattern:
            self._pattern = pattern

    @classmethod
    def from_yaml(cls, name, test_plan, file_systems, default_filters=None):
        kw = {
            'name': name,
            'rootfs': file_systems[test_plan['rootfs']],
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
            protocol=self.rootfs.boot_protocol,
            rootfs=self.rootfs.root_type,
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


# -----------------------------------------------------------------------------
# Entry points
#

def builds_from_yaml(yaml_path):
    with open(yaml_path) as f:
        data = yaml.load(f)

    trees = {
        name: Tree.from_yaml(config, name)
        for name, config in data['trees'].iteritems()
    }

    fragments = {
        name: Fragment.from_yaml(config, name)
        for name, config in data.get('fragments', {}).iteritems()
    }

    build_environments = {
        name: BuildEnvironment.from_yaml(config, name)
        for name, config in data['build_environments'].iteritems()
    }

    defaults = data.get('build_configs_defaults', {})

    build_configs = {
        name: BuildConfig.from_yaml(config, name, trees, fragments,
                                    build_environments, defaults)
        for name, config in data['build_configs'].iteritems()
    }

    config_data = {
        'trees': trees,
        'fragments': fragments,
        'build_environments': build_environments,
        'build_configs': build_configs,
    }

    return config_data


def tests_from_yaml(yaml_path):
    with open(yaml_path) as f:
        data = yaml.load(f)

    fs_types = {
        name: RootFSType.from_yaml(fs_type)
        for name, fs_type in data['file_system_types'].iteritems()
    }

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

    config_data = {
        'file_systems': file_systems,
        'test_plans': test_plans,
        'device_types': device_types,
        'test_configs': test_configs,
    }

    return config_data
