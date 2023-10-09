# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for the KernelCI TOML settings"""

import kernelci.settings


def test_load_toml():
    """Verify that the settings can be loaded from the local TOML file"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')
    assert settings.path == 'tests/kernelci-settings.toml'


def test_get_raw():
    """Test the Settings.get_raw() method with various use-cases"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')
    something = settings.get_raw('something')
    assert something == 'hello'
    value_int = settings.get_raw('kci', 'hello')
    assert value_int == 123
    value_bool = settings.get_raw('kci', 'flag')
    assert value_bool is False
    value_str = settings.get_raw('kci', 'name')
    assert value_str == 'bingo'
    value_sub_command = settings.get_raw('kci', 'foo', 'bar')
    assert value_sub_command == 456
    value_not_found = settings.get_raw('kci', 'foo', 'baz')
    assert value_not_found is None
    abc = settings.get_raw('kci', 'foo', 'a', 'b', 'c')
    assert abc == 'ABC'
    xyz = settings.get_raw('kci', 'foo', 'a', 'b', 'z')
    assert xyz == 'XYZ'
    ab_group = settings.get_raw('kci', 'foo', 'a', 'b')
    assert ab_group == {'c': 'ABC', 'z': 'XYZ'}
    alt = settings.get_raw('alternative', 'foo', 'bar')
    assert alt == 'baz'
