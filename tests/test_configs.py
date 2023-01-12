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


def test_trees():
    # ToDo: use relative path to test module 'configs/trees.yaml'
    yaml_file_path = 'tests/configs/trees.yaml'
    with open(yaml_file_path) as yaml_file:
        ref_data = yaml.safe_load(yaml_file)
    tree_names = ['kselftest', 'mainline', 'next']
    assert all(name in ref_data['trees'] for name in tree_names)
    config = kernelci.config.load(yaml_file_path)
    trees_dump = yaml.dump(config['trees'])
    trees_config = yaml.safe_load(trees_dump)
    assert all(name in trees_config for name in tree_names)
    assert ref_data['trees'] == trees_config
    assert (
        trees_config['next']['url'] ==
        'https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git'
    )


def test_file_system_types():
    yaml_file_path = 'tests/configs/file-system-types.yaml'
    with open(yaml_file_path) as yaml_file:
        ref_data = yaml.safe_load(yaml_file)
    fs_names = ['buildroot', 'debian']
    assert all(name in ref_data['file_system_types'] for name in fs_names)
    config = kernelci.config.load(yaml_file_path)
    fs_dump = {
        name: config.to_yaml()
        for name, config in config['file_system_types'].items()
    }
    fs_config = {
        name: yaml.safe_load(config) for name, config in fs_dump.items()
    }
    assert all(name in fs_config for name in fs_names)
    assert ref_data['file_system_types'] == fs_config
    assert (
        fs_config['debian']['url'] ==
        'http://storage.kernelci.org/images/rootfs/debian'
    )
