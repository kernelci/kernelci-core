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

import kernelci.config
import kernelci.config.build
import kernelci.config.test


def test_build_configs_parsing():
    """ Verify build configs from YAML"""
    data = kernelci.config.load_yaml("config/core")
    configs = kernelci.config.build.from_yaml(data)
    assert len(configs) == 4
    for key in ['build_configs', 'build_environments', 'fragments', 'trees']:
        assert key in configs
        assert len(configs[key]) > 0


def test_build_configs_parsing_minimal():
    data = kernelci.config.load_yaml("tests/configs/builds-minimal.yaml")
    configs = kernelci.config.build.from_yaml(data)
    assert 'agross' in configs['build_configs']
    assert 'agross' in configs['trees']
    assert 'gcc-7' in configs['build_environments']
    assert len(configs['fragments']) == 0


def test_build_configs_parsing_empty_architecture():
    data = kernelci.config.load_yaml("tests/configs/builds-empty-arch.yaml")
    configs = kernelci.config.build.from_yaml(data)
    assert len(configs) == 4


def test_architecture_init_name_only():
    architecture = kernelci.config.build.Architecture("arm")
    assert architecture.name == 'arm'
    assert architecture.base_defconfig == 'defconfig'
    assert architecture.extra_configs == []
    assert architecture.fragments == []
    assert architecture._filters == []  # filters does not have a property..
