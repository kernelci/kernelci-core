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
    abc = settings.get_raw('kci', 'foo', 'a', 'b', 'c')
    assert abc == 'ABC'
    xyz = settings.get_raw('kci', 'foo', 'a', 'b', 'z')
    assert xyz == 'XYZ'
    ab_group = settings.get_raw('kci', 'foo', 'a', 'b')
    assert ab_group == {'c': 'ABC', 'z': 'XYZ'}
    alt = settings.get_raw('alternative', 'foo', 'bar')
    assert alt == 'baz'


def test_get():
    """Test the Settings.get() method with various use-cases"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')
    raw_flag = settings.get_raw('kci', 'foo', 'flag')
    assert raw_flag is None
    parent_flag = settings.get('kci', 'foo', 'flag')
    assert parent_flag is False
    raw_name = settings.get_raw('kci', 'foo', 'name')
    assert raw_name is None
    parent_name = settings.get('kci', 'foo', 'name')
    assert parent_name == 'bingo'
    alt_bar = settings.get('alternative', 'foo', 'bar')
    assert alt_bar == 'baz'
    alt_hello = settings.get('alternative', 'hello')
    assert alt_hello == 456
    abc = settings.get('alternative', 'hey', 'abc')
    assert abc == 'def'
    hello = settings.get('alternative', 'hey', 'hello')
    assert hello == 456


def test_not_found():
    """Test all the Settings methods with values that don't exist"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')
    assert settings.get_raw('kci', 'foo', 'baz') is None
    assert settings.get_raw('kci', 'foo', 'baz', 'bingo') is None
    assert settings.get_raw('kci', 'what') is None
    assert settings.get_raw('something', 'else') is None
    assert settings.get('kci', 'what') is None
    assert settings.get('what') is None
    assert settings.get('something', 'else') is None
    assert settings.get() is None


def test_secrets_init():
    """Verify that secrets can be initialised from the TOML settings"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')
    secrets = kernelci.settings.Secrets(settings)
    assert secrets.root == ()
    assert secrets.ding.dong is None


def test_secrets():
    """Test that secrets can be retrieved from the TOML settings"""
    settings = kernelci.settings.Settings('tests/kernelci-settings.toml')

    args = {
        'storage': 'foo',
        'api': 'main',
    }
    secrets = kernelci.settings.Secrets(settings, args, ('kci', 'secrets'))
    assert secrets.storage.password == 'abracadabra'
    assert secrets.api.token == 'my-main-api-token'

    args = {
        'storage': 'bar',
        'api': 'local',
    }
    secrets = kernelci.settings.Secrets(settings, args, ('kci', 'secrets'))
    assert secrets.storage.password == 'mickeymouse'
    assert secrets.api.token == 'my-local-api-token'
    assert secrets.storage.nothing is None
    assert secrets.wrong.path is None

    args = {
        'foo': 'bar',
    }
    secrets = kernelci.settings.Secrets(settings, args, ('secret', 'bits'))
    assert secrets.foo.baz == 'FooBarBaz'
    assert secrets.bar.baz is None
