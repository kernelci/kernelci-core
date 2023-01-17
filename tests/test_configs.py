# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021 Collabora Limited
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

import unittest
import yaml

import kernelci.config
import kernelci.config.build
import kernelci.config.test


def test_build_configs_parsing():
    """ Verify build configs from YAML"""
    data = kernelci.config.load_yaml("config/core")
    configs = kernelci.config.build.from_yaml(data, {})
    assert len(configs) == 4
    for key in ['build_configs', 'build_environments', 'fragments', 'trees']:
        assert key in configs
        assert len(configs[key]) > 0


def test_build_configs_parsing_minimal():
    data = kernelci.config.load_yaml("tests/configs/builds-minimal.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert 'agross' in configs['build_configs']
    assert 'agross' in configs['trees']
    assert 'gcc-7' in configs['build_environments']
    assert len(configs['fragments']) == 0


def test_build_configs_parsing_empty_architecture():
    data = kernelci.config.load_yaml("tests/configs/builds-empty-arch.yaml")
    configs = kernelci.config.build.from_yaml(data, {})
    assert len(configs) == 4


def test_architecture_init_name_only():
    architecture = kernelci.config.build.Architecture("arm")
    assert architecture.name == 'arm'
    assert architecture.base_defconfig == 'defconfig'
    assert architecture.extra_configs == []
    assert architecture.fragments == []
    assert architecture._filters == []  # filters does not have a property..


class ConfigTest(unittest.TestCase):

    def _load_config(self, yaml_file_path):
        with open(yaml_file_path) as yaml_file:
            ref_data = yaml.safe_load(yaml_file)
        config = kernelci.config.load(yaml_file_path)
        return ref_data, config

    def _reload(self, ref_data, config, name):
        assert name in config
        assert name in ref_data
        dump = yaml.dump(config[name])
        loaded = yaml.safe_load(dump)
        assert ref_data[name] == loaded
        return loaded


class BuildConfigTest(ConfigTest):

    def test_trees(self):
        # ToDo: use relative path to test module 'configs/trees.yaml'
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
        ref_data, config = self._load_config('tests/configs/fragments.yaml')
        frag_config = self._reload(ref_data, config, 'fragments')
        frag_names = ['debug', 'ima', 'x86-chromebook', 'x86_kvm_guest']
        assert all(name in ref_data['fragments'] for name in frag_names)
        assert all(name in frag_config for name in frag_names)
        assert frag_config['debug']['path'] == 'kernel/configs/debug.config'

    def test_build_environments(self):
        ref_data, config = self._load_config(
            'tests/configs/build-environments.yaml'
        )
        be_config = self._reload(ref_data, config, 'build_environments')
        be_names = ['gcc-10', 'clang-11', 'clang-15', 'rustc-1.62']
        assert all(name in ref_data['build_environments'] for name in be_names)
        assert all(name in be_config for name in be_names)
        assert be_config['clang-15']['cc_version'] == '15'

    def test_reference_tree(self):
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
        ref_data, config = self._load_config('tests/configs/builds.yaml')
        build_configs = self._reload(ref_data, config, 'build_configs')
        config_names = ['arm64', 'mainline']
        assert all(name in ref_data['build_configs'] for name in config_names)
        assert all(name in build_configs for name in config_names)
        assert build_configs['mainline']['tree'] == 'mainline'


class TestConfigTest(ConfigTest):

    def test_file_system_types(self):
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


class APIConfigTest(ConfigTest):

    def test_apis(self):
        ref_data, config = self._load_config('tests/configs/api-configs.yaml')
        api_config = self._reload(ref_data, config, 'api_configs')
        api_names = ['docker-host']
        assert all(name in ref_data['api_configs'] for name in api_names)
        assert all(name in api_config for name in api_names)
        assert (
            api_config['docker-host']['url'] == 'http://172.17.0.1:8001'
        )
