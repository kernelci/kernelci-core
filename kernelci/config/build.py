# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2018-2026 Collabora Limited
#
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""Build configuration classes for kernel builds"""

from .base import FilterFactory, YAMLConfigObject


class Tree(YAMLConfigObject):
    """Kernel git tree model."""

    yaml_tag = '!Tree'

    def __init__(self, name, url):
        """A kernel git tree is essentially a repository with kernel branches.

        *name* is the name of the tree, such as "mainline" or "next".
        *url* is the git remote URL for the tree.
        """
        self._name = name
        self._url = url

    @property
    def name(self):
        """Return the tree name."""
        return self._name

    @property
    def url(self):
        """Return the tree URL."""
        return self._url

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'url'})
        return attrs


class Fragment(YAMLConfigObject):
    """Kernel config fragment model."""

    yaml_tag = '!Fragment'

    def __init__(self, name, path, *, configs=None, defconfig=None):
        """A kernel config fragment is a list of config options in file.

        *name* is the name of the config fragment so it can be referred to in
               other configuration objects.

        *path* is the path where the config fragment either can be found,
               either from the git checkout or after being generated.

        *configs* is an optional list of kernel configs to use when generating
                  a config fragment that does not exist in the git checkout.

        *defconfig* is an optional defconfig name to use as a make target
                    instead of a real config path.
        """
        self._name = name
        self._path = path
        self._configs = configs or []
        self._defconfig = defconfig

    @property
    def name(self):
        """Return the fragment name."""
        return self._name

    @property
    def path(self):
        """Return the fragment path."""
        return self._path

    @property
    def configs(self):
        """Return a copy of the fragment configs."""
        return list(self._configs)

    @property
    def defconfig(self):
        """Return the default defconfig name."""
        return self._defconfig

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'path', 'configs', 'defconfig'})
        return attrs


class BuildEnvironment(YAMLConfigObject):
    """Kernel build environment model."""

    yaml_tag = '!BuildEnvironment'

    def __init__(self, name, cc, cc_version, *, arch_params=None):
        """A build environment is a compiler and tools to build a kernel.

        *name* is the name of the build environment so it can be referred to in
               other parts of the build configuration.

        *cc* is the compiler type, such as "gcc" or "clang".

        *cc_version* is the full version of the compiler.

        *arch_params* is a dictionary with parameters for each CPU architecture.
        """
        self._name = name
        self._cc = cc
        self._cc_version = str(cc_version)
        self._arch_params = arch_params or {}

    @property
    def name(self):
        """Return the build environment name."""
        return self._name

    @property
    def cc(self):
        """Return the compiler name."""
        return self._cc

    @property
    def cc_version(self):
        """Return the compiler version."""
        return self._cc_version

    @property
    def arch_params(self):
        """Return a copy of architecture parameters."""
        return {arch: params.copy() for arch, params in self._arch_params.items()}

    @classmethod
    def _get_yaml_attributes(cls):
        attrs = super()._get_yaml_attributes()
        attrs.update({'cc', 'cc_version', 'arch_params'})
        return attrs

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                'cc': data.cc,
                'cc_version': data.cc_version,
                'arch_params': data.arch_params,
            }
        )

    def get_arch_param(self, arch, param):
        """Get architecture-specific parameter value."""
        arch_params = self._arch_params.get(arch, {})
        param_value = arch_params.get(param)
        if isinstance(param_value, dict):
            return param_value.copy()
        return param_value


class Architecture(YAMLConfigObject):
    """CPU architecture attributes."""

    yaml_tag = '!Architecture'

    def __init__(  # pylint: disable=too-many-arguments
        self, name, *, base_defconfig='defconfig', extra_configs=None,
        fragments=None, filters=None
    ):
        """Particularities to build kernels for each CPU architecture.

        *name* is the CPU architecture name as per the kernel's convention.

        *base_defconfig* is the defconfig used by default and as a basis when
                         adding fragments.

        *extra_configs* is a list of extra defconfigs and make targets to build.

        *fragments* is a list of CPU-specific config fragments to build.

        *filters* is a list of filters to limit the number of builds.
        """
        self._name = name
        self._base_defconfig = base_defconfig
        self._extra_configs = extra_configs or []
        self._fragments = fragments or []
        self._filters = filters or []

    @classmethod
    def load_from_yaml(cls, config, name, fragments):  # pylint: disable=arguments-differ
        """Load Architecture from YAML with fragment references."""
        kw = {'name': name}
        kw.update(cls._kw_from_yaml(config, [
            'base_defconfig', 'extra_configs',
        ]))
        frag_names = config.get('fragments') if config else None
        kw['fragments'] = [fragments[n] for n in frag_names] if frag_names else None
        kw['filters'] = FilterFactory.from_data(config or {})
        return cls(**kw)

    @property
    def name(self):
        """Return the architecture name."""
        return self._name

    @property
    def base_defconfig(self):
        """Return the base defconfig name."""
        return self._base_defconfig

    @property
    def extra_configs(self):
        """Return the extra configs list."""
        return list(self._extra_configs)

    @property
    def fragments(self):
        """Return the fragment list."""
        return list(self._fragments)

    @property
    def filters(self):
        """Return the filters list."""
        return list(self._filters)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                'base_defconfig': data.base_defconfig,
                'extra_configs': data.extra_configs,
                'fragments': [frag.name for frag in data.fragments],
                'filters': [{fil.name: fil} for fil in data.filters],
            }
        )

    def match(self, params):
        """Check if parameters match the filters."""
        return all(f.match(**params) for f in self._filters)


class Reference(YAMLConfigObject):
    """Kernel reference tree and branch model."""

    yaml_tag = '!Reference'

    def __init__(self, tree, branch):
        """Reference is a tree and branch used for bisections.

        *tree* is a Tree object.
        *branch* is the branch name to be used from the tree.
        """
        self._tree = tree
        self._branch = branch

    @classmethod
    def load_from_yaml(cls, reference, trees):  # pylint: disable=arguments-differ
        """Load Reference from YAML with tree reference."""
        kw = cls._kw_from_yaml(reference, ['tree', 'branch'])
        kw['tree'] = trees[kw['tree']]
        return cls(**kw)

    @property
    def tree(self):
        """Return the reference tree."""
        return self._tree

    @property
    def branch(self):
        """Return the reference branch."""
        return self._branch

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                'tree': data.tree.name,
                'branch': data.branch,
            }
        )


class BuildVariant(YAMLConfigObject):
    """A variant of a given build configuration."""

    yaml_tag = '!BuildVariant'

    def __init__(self, name, architectures, build_environment, *, fragments=None):
        """A build variant is a sub-section of a build configuration.

        *name* is the name of the build variant.

        *architectures* is a list of Architecture objects.

        *build_environment* is a BuildEnvironment object.

        *fragments* is an optional list of Fragment objects.
        """
        self._name = name
        self._architectures = {arch.name: arch for arch in architectures}
        self._build_environment = build_environment
        self._fragments = fragments or []

    @classmethod
    def load_from_yaml(  # pylint: disable=arguments-differ
        cls, config, name, fragments, build_environments
    ):
        """Load BuildVariant from YAML with references."""
        kw = {'name': name}
        kw.update(cls._kw_from_yaml(config, ['build_environment']))
        kw['build_environment'] = build_environments[kw['build_environment']]
        kw['architectures'] = [
            Architecture.load_from_yaml(data or {}, arch_name, fragments)
            for arch_name, data in config['architectures'].items()
        ]
        frag_names = kw.get('fragments')
        if frag_names:
            kw['fragments'] = [fragments[n] for n in frag_names]
        else:
            frag_names = config.get('fragments')
            kw['fragments'] = [fragments[n] for n in frag_names] if frag_names else None
        return cls(**kw)

    @property
    def name(self):
        """Return the variant name."""
        return self._name

    @property
    def arch_list(self):
        """Return the architecture names list."""
        return list(self._architectures.keys())

    @property
    def architectures(self):
        """Return the architecture objects list."""
        return list(self._architectures.values())

    def get_arch(self, arch_name):
        """Return an architecture by name."""
        return self._architectures.get(arch_name)

    @property
    def build_environment(self):
        """Return the build environment."""
        return self._build_environment

    @property
    def fragments(self):
        """Return the variant fragments list."""
        return list(self._fragments)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(
            'tag:yaml.org,2002:map', {
                'build_environment': data.build_environment.name,
                'fragments': [frag.name for frag in data.fragments],
                'architectures': {arc.name: arc for arc in data.architectures},
            }
        )


class BuildConfig(YAMLConfigObject):
    """Build configuration model."""

    yaml_tag = '!BuildConfig'

    def __init__(  # pylint: disable=too-many-arguments
        self, name, tree, branch, variants, *, reference=None,
        architectures=None, frequency=None
    ):
        """A build configuration defines the actual kernels to be built.

        *name* is the name of the build configuration.

        *tree* is a Tree object.

        *branch* is the name of the branch to build.

        *variants* is a dict of BuildVariant objects.

        *reference* is a Reference object for bisections.

        *architectures* is an optional list of architectures to filter.

        *frequency* is an optional string that limits how often a checkout node
                    can be created. Format: [Nd][Nh][Nm]
        """
        self._name = name
        self._tree = tree
        self._branch = branch
        self._variants = variants
        self._reference = reference
        self._architectures = architectures
        self._frequency = frequency

    @classmethod
    # pylint: disable=arguments-differ,too-many-arguments,too-many-positional-arguments
    def load_from_yaml(cls, config, name, trees, fragments, b_envs, defaults):
        """Load BuildConfig from YAML with all references."""
        kw = {'name': name}
        kw.update(cls._kw_from_yaml(config, ['tree', 'branch']))
        kw['tree'] = trees[kw['tree']]

        default_variants = defaults.get('variants', {})
        config_variants = config.get('variants', default_variants)
        variants = [
            BuildVariant.load_from_yaml(variant, var_name, fragments, b_envs)
            for var_name, variant in config_variants.items()
        ]
        kw['variants'] = {v.name: v for v in variants}

        reference = config.get('reference', defaults.get('reference'))
        if reference:
            kw['reference'] = Reference.load_from_yaml(reference, trees)

        kw['architectures'] = config.get('architectures')
        kw['frequency'] = config.get('frequency')
        return cls(**kw)

    @property
    def name(self):
        """Return the build config name."""
        return self._name

    @property
    def tree(self):
        """Return the build config tree."""
        return self._tree

    @property
    def branch(self):
        """Return the build config branch."""
        return self._branch

    @property
    def variants(self):
        """Return the build config variants list."""
        return list(self._variants.values())

    @property
    def architectures(self):
        """Return the architecture filter list."""
        return self._architectures

    def get_variant(self, name):
        """Return a build variant by name."""
        return self._variants[name]

    @property
    def reference(self):
        """Return the build config reference."""
        return self._reference

    @property
    def frequency(self):
        """Return the checkout frequency."""
        return self._frequency

    @classmethod
    def to_yaml(cls, dumper, data):
        result = {
            'tree': data.tree.name,
            'branch': data.branch,
            'variants': {var.name: var for var in data.variants},
            'reference': data.reference,
        }
        if data.frequency:
            result['frequency'] = data.frequency
        return dumper.represent_mapping('tag:yaml.org,2002:map', result)


def from_yaml(data, _):
    """Load build configuration from YAML data.

    Returns a dictionary with:
    - trees: dict of Tree objects
    - fragments: dict of Fragment objects
    - build_environments: dict of BuildEnvironment objects
    - build_configs: dict of BuildConfig objects
    """
    trees = {
        name: Tree.load_from_yaml(config, name=name)
        for name, config in data.get('trees', {}).items()
    }

    fragments = {
        name: Fragment.load_from_yaml(config, name=name)
        for name, config in data.get('fragments', {}).items()
    }

    build_environments = {
        name: BuildEnvironment.load_from_yaml(config, name=name)
        for name, config in data.get('build_environments', {}).items()
    }

    defaults = data.get('build_configs_defaults', {})

    build_configs = {
        name: BuildConfig.load_from_yaml(
            config, name, trees, fragments, build_environments, defaults
        )
        for name, config in data.get('build_configs', {}).items()
    }

    return {
        'trees': trees,
        'fragments': fragments,
        'build_environments': build_environments,
        'build_configs': build_configs,
    }
