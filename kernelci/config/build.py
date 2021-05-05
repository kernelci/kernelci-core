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


class Reference(YAMLObject):
    """Kernel reference tree and branch model."""

    def __init__(self, tree, branch):
        """Reference is a tree and branch used for bisections

        *tree* is a Tree object
        *branch* is the branch name to be used from the tree
        """
        self._tree = tree
        self._branch = branch

    @classmethod
    def from_yaml(cls, reference, trees):
        kw = cls._kw_from_yaml(reference, ['tree', 'branch'])
        kw['tree'] = trees[kw['tree']]
        return cls(**kw)

    @property
    def tree(self):
        return self._tree

    @property
    def branch(self):
        return self._branch


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
                  using a list of defconfigs to blocklist or passlist.
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

    def __init__(self, name, cc, cc_version, arch_params=None):
        """A build environment is a compiler and tools to build a kernel.

        *name* is the name of the build environment so it can be referred to in
               other parts of the build configuration.  Typical build
               environment names include the compiler type and version such as
               "gcc-7" although this is entirely arbitrary.

        *cc* is the compiler type, such as "gcc" or "clang".  This is
            functional and indicates the actual compiler binary being used.

        *cc_version* is the full version of the compiler.

        *arch_params* is a dictionary with parameters for each CPU architecture
                      using names defined in the kernel.  For example, gcc
                      compilers use the same "x86" architecture name "x86" for
                      both "i386" and "x86_64" kernel architectures.
        """
        self._name = name
        self._cc = cc
        self._cc_version = str(cc_version)
        self._arch_params = arch_params or dict()

    @classmethod
    def from_yaml(cls, config, name):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(
            config, ['name', 'cc', 'cc_version', 'arch_params']))
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
        params = self._arch_params.get(kernel_arch) or dict()
        return params.get('name', kernel_arch)

    def get_arch_opts(self, arch):
        params = self._arch_params.get(arch) or dict()
        return params.get('opts') or dict()

    def get_cross_compile(self, arch):
        params = self._arch_params.get(arch) or dict()
        return params.get('cross_compile', '')

    def get_cross_compile_compat(self, arch):
        params = self._arch_params.get(arch) or dict()
        return params.get('cross_compile_compat', '')


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
            for name, data in config['architectures'].items()
        )
        cf = kw.get('fragments')
        kw['fragments'] = [fragments[name] for name in cf] if cf else None
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def arch_list(self):
        return list(self._architectures.keys())

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

    def __init__(self, name, tree, branch, variants, reference=None):
        """A build configuration defines the actual kernels to be built.

        *name* is the name of the build configuration.  It is arbitrary and
               used in other places to refer to the build configuration.

        *tree* is a Tree object, where the kernel branche to be built can be
               found.

        *branch* is the name of the branch to build.  There can only be one
                 branch in each BuildConfig object.

        *variants* is a list of BuildVariant objects, to define all the
                   variants to build for this tree / branch combination.

        *reference* is a Reference object which defines the tree and branch for
                    bisections when no base commit is found for the good and
                    bad revisions.  It can also be None if no reference branch
                    can be used with this build configuration.
        """
        self._name = name
        self._tree = tree
        self._branch = branch
        self._variants = variants
        self._reference = reference

    @classmethod
    def from_yaml(cls, config, name, trees, fragments, build_envs, defaults):
        kw = {
            'name': name,
        }
        kw.update(cls._kw_from_yaml(
            config, ['name', 'tree', 'branch']))
        kw['tree'] = trees[kw['tree']]
        default_variants = defaults.get('variants', {})
        config_variants = config.get('variants', default_variants)
        variants = [
            BuildVariant.from_yaml(variant, name, fragments, build_envs)
            for name, variant in config_variants.items()
        ]
        kw['variants'] = {v.name: v for v in variants}
        reference = config.get('reference', defaults.get('reference'))
        if reference:
            kw['reference'] = Reference.from_yaml(reference, trees)
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

    @property
    def reference(self):
        return self._reference


def from_yaml(yaml_path):
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    trees = {
        name: Tree.from_yaml(config, name)
        for name, config in data['trees'].items()
    }

    fragments = {
        name: Fragment.from_yaml(config, name)
        for name, config in data.get('fragments', {}).items()
    }

    build_environments = {
        name: BuildEnvironment.from_yaml(config, name)
        for name, config in data['build_environments'].items()
    }

    defaults = data.get('build_configs_defaults', {})

    build_configs = {
        name: BuildConfig.from_yaml(config, name, trees, fragments,
                                    build_environments, defaults)
        for name, config in data['build_configs'].items()
    }

    config_data = {
        'trees': trees,
        'fragments': fragments,
        'build_environments': build_environments,
        'build_configs': build_configs,
    }

    return config_data
