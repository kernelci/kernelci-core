# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for KernelCI YAML config handling"""

# This is normal practice for tests in order to cover parts of the
# implementation.
# pylint: disable=protected-access
#
# For the test classes with only one test case...
# pylint: disable=too-few-public-methods

import yaml

import kernelci.config
import kernelci.config.build


def test_build_configs_parsing():
    """Verify build configs from YAML"""
    data = kernelci.config.load_yaml("config/core")
    configs = kernelci.config.build.from_yaml(data, {})
    assert len(configs) == 4
    for key in ['build_configs', 'build_environments', 'fragments', 'trees']:
        assert key in configs
        assert len(configs[key]) > 0


def test_build_configs_parsing_minimal():
    """Test that minimal build configs can be parsed from YAML"""
    data = kernelci.config.load_yaml("tests/configs/builds-minimal.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert 'agross' in configs['build_configs']
    assert 'agross' in configs['trees']
    assert 'gcc-7' in configs['build_environments']
    assert len(configs['fragments']) == 0


def test_build_configs_parsing_empty_architecture():
    """Test that build configs with empty architectures can be parsed"""
    data = kernelci.config.load_yaml("tests/configs/builds-empty-arch.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert len(configs) == 4


def test_architecture_init_name_only():
    """Test that build config objects can be created with just a name"""
    architecture = kernelci.config.build.Architecture("arm")
    assert architecture.name == 'arm'
    assert architecture.base_defconfig == 'defconfig'
    assert len(architecture.extra_configs) == 0
    assert len(architecture.fragments) == 0
    assert len(architecture._filters) == 0


class ConfigTest:  # pylint: disable=too-few-public-methods
    """Base class with helpers for all YAML configuration tests"""

    @classmethod
    def _load_config(cls, yaml_file_path):
        with open(yaml_file_path, encoding='utf-8') as yaml_file:
            ref_data = yaml.safe_load(yaml_file)
        config = kernelci.config.load(yaml_file_path)
        return ref_data, config

    @classmethod
    def _reload(cls, ref_data, config, name):
        assert name in config
        assert name in ref_data
        dump = yaml.dump(config[name])
        loaded = yaml.safe_load(dump)
        assert ref_data[name] == loaded
        return loaded


class TestBuildConfigs(ConfigTest):
    """Tests for configs related to builds"""

    def test_trees(self):
        """Test the tree configs"""
        ref_data, config = self._load_config('tests/configs/trees.yaml')
        trees_config = self._reload(ref_data, config, 'trees')
        tree_names = ['kselftest', 'mainline', 'next']
        assert all(name in ref_data['trees'] for name in tree_names)
        assert all(name in trees_config for name in tree_names)
        assert (
            trees_config['next']['url'] ==
            'https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git'  # noqa
        )

    def test_fragments(self):
        """Test the fragments configs"""
        ref_data, config = self._load_config('tests/configs/fragments.yaml')
        frag_config = self._reload(ref_data, config, 'fragments')
        frag_names = ['debug', 'ima', 'x86-chromebook', 'x86_kvm_guest']
        assert all(name in ref_data['fragments'] for name in frag_names)
        assert all(name in frag_config for name in frag_names)
        assert frag_config['debug']['path'] == 'kernel/configs/debug.config'

    def test_build_environments(self):
        """Test the build_environments configs"""
        ref_data, config = self._load_config(
            'tests/configs/build-environments.yaml'
        )
        be_config = self._reload(ref_data, config, 'build_environments')
        be_names = ['gcc-10', 'clang-11', 'clang-12', 'rustc-1.62']
        assert all(name in ref_data['build_environments'] for name in be_names)
        assert all(name in be_config for name in be_names)
        assert be_config['clang-12']['cc_version'] == '12'
        clang12 = config['build_environments']['clang-12']
        assert (
            clang12.get_arch_param('arm64', 'cross_compile_compat') ==
            'arm-linux-gnueabihf-'
        )
        assert (
            clang12.get_arch_param('riscv', 'opts')['LLVM_IAS'] == '1'
        )

    def test_reference_tree(self):
        """Test the build_configs reference tree configs"""
        ref_data, config = self._load_config('tests/configs/builds.yaml')
        assert 'build_configs' in ref_data
        build_configs = ref_data['build_configs']
        assert 'arm64' in build_configs
        arm64 = build_configs['arm64']
        assert 'reference' in arm64
        reference = arm64['reference']
        reference_config = config['build_configs']['arm64'].reference
        assert reference_config.tree.name == 'mainline'
        reference_dump = yaml.dump(reference_config)
        reference_check = yaml.safe_load(reference_dump)
        assert reference == reference_check

    def test_build_configs(self):
        """Test the build_configs"""
        ref_data, config = self._load_config('tests/configs/builds.yaml')
        build_configs = self._reload(ref_data, config, 'build_configs')
        config_names = ['arm64', 'mainline']
        assert all(name in ref_data['build_configs'] for name in config_names)
        assert all(name in build_configs for name in config_names)
        assert build_configs['mainline']['tree'] == 'mainline'


class TestTestConfigs(ConfigTest):
    """Tests for configs related to runtime tests"""

    def test_file_system_types(self):
        """Test the file_system_types configs"""
        ref_data, config = self._load_config(
            'tests/configs/file-system-types.yaml'
        )
        fs_config = self._reload(ref_data, config, 'file_system_types')
        fs_names = ['buildroot', 'debian']
        assert all(name in ref_data['file_system_types'] for name in fs_names)
        assert all(name in fs_config for name in fs_names)
        assert (
            fs_config['debian']['url'] ==
            'http://storage.kernelci.org/images/rootfs/debian'
        )


class TestAPIConfigs(ConfigTest):
    """Tests for configs related to the KernelCI API"""

    def test_apis(self):
        """Test the api_configs"""
        ref_data, config = self._load_config('tests/configs/api-configs.yaml')
        api_config = self._reload(ref_data, config, 'api_configs')
        api_names = ['docker-host']
        assert all(name in ref_data['api_configs'] for name in api_names)
        assert all(name in api_config for name in api_names)
        assert (
            api_config['docker-host']['url'] == 'http://172.17.0.1:8001'
        )


class TestRuntimeConfigs(ConfigTest):
    """Tests related to runtime configs"""

    def test_lab(self):
        """Test the labs configs"""
        _, config = self._load_config('tests/configs/labs.yaml')
        labs = config['labs']
        lab_prio = {
            'lab-baylibre': (None, None, None),
            'lab-broonie': (None, 0, 40),
            'lab-collabora-staging': (45, 45, 45),
        }
        assert all(name in labs for name, _ in lab_prio.items())
        for lab_name, (fixed_p, min_p, max_p) in lab_prio.items():
            lab_config = labs[lab_name]
            assert lab_config.priority == fixed_p
            assert lab_config.priority_min == min_p
            assert lab_config.priority_max == max_p
