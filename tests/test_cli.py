# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for the KernelCI command line tools"""

import pytest

import click

import kernelci.cli
import kernelci.settings


def test_command_settings_init():
    """Verify that the CommandSettings class can be initialised"""
    ctx = kernelci.cli.CommandSettings('tests/kernelci-cli.toml')
    assert ctx is not None
    secrets = ctx.get_secrets({}, ())
    assert secrets is not None
    assert isinstance(secrets, kernelci.settings.Secrets)


def test_kci_command():
    """Test the kernelci.cli.Kci base class"""

    @kernelci.cli.kci.command(cls=kernelci.cli.Kci, help="Unit test")
    @click.option('--hello', type=int)
    @click.option('--hack', type=str)
    def hey(hello, hack):
        assert isinstance(hello, int)
        assert hello == 123
        assert isinstance(hack, str)
        assert hack == 'Hack'

    try:
        kernelci.cli.kci(args=[  # pylint: disable=no-value-for-parameter
            '--toml-settings', 'tests/kernelci-cli.toml',
            'hey', '--hack', 'Hack'
        ])
    except SystemExit as exc:
        if exc.code != 0:
            raise exc


def test_kci_command_with_secrets():
    """Test the kernelci.cli.KciS class"""

    @kernelci.cli.kci.command(cls=kernelci.cli.KciS, help="With secrets")
    @click.option('--foo', type=str)
    def cmd(foo, secrets):  # pylint: disable=disallowed-name
        assert isinstance(foo, str)
        assert foo == 'bar'
        assert secrets.foo.baz == 'FooBarBaz'

    try:
        kernelci.cli.kci(args=[  # pylint: disable=no-value-for-parameter
            '--toml-settings', 'tests/kernelci-cli.toml',
            'cmd', '--foo', 'bar'
        ])
    except SystemExit as exc:
        if exc.code != 0:
            raise exc


def test_split_valid_attributes():
    """Test the logic to split valid attribute with operators"""
    attributes = [
        (['name=value'], {'name': 'value'}),
        (['name>value'], {'name__gt': 'value'}),
        (['name>=value'], {'name__gte': 'value'}),
        (['name<value'], {'name__lt': 'value'}),
        (['name<=value'], {'name__lte': 'value'}),
        (['name = value'], {'name': 'value'}),
        (['name =value'], {'name': 'value'}),
        (['name >= value'], {'name__gte': 'value'}),
        (['name>= value'], {'name__gte': 'value'}),
        (['a=b', 'c=123', 'x3 = 1.2', 'abc >= 4', 'z != x[2]'], {
            'a': 'b', 'c': '123', 'x3': '1.2', 'abc__gte': '4', 'z__ne': 'x[2]'
        }),
    ]
    for attrs, parsed in attributes:
        print(attrs, parsed)
        result = kernelci.cli.split_attributes(attrs)
        assert result == parsed


def test_split_invalid_attributes():
    """Test the logic to split invalid attribute with operators"""
    attributes = [
        ['key == something'],
        ['key==else'],
        ['key== else'],
        ['x ==a'],
        ['wr?ong = other'],
        ['wrong| = other'],
        ['foo=>bar'],
        ['foo=<bar'],
        ['foo<>bar'],
        ['foo=!bar'],
        ['a=1', 'a=again'],
        ['key = 123', 'key >= 456']
    ]
    for attrs in attributes:
        with pytest.raises(click.ClickException):
            kernelci.cli.split_attributes(attrs)
