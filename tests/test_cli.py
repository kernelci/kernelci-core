# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for the KernelCI command line tools"""

import pytest

import click
import requests

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
    @click.option('--many', type=str, multiple=True)
    @click.option('--more', type=str, multiple=True)
    def hey(hello, hack, many, more):
        assert isinstance(hello, int)
        assert hello == 123
        assert isinstance(hack, str)
        assert hack == 'Hack'
        assert isinstance(many, list)
        assert many == ['a', 'bcd', 'xzy']
        assert isinstance(more, list)
        assert more == ['xyz', 'abc']

    try:
        kernelci.cli.kci(args=[  # pylint: disable=no-value-for-parameter
            '--toml-settings', 'tests/kernelci-cli.toml',
            'hey', '--hack', 'Hack', '--more=xyz', '--more=abc'
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
        (None, {}),
        ([], {}),
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
        (['x>=1', 'x<=3'], {'x__gte': '1', 'x__lte': '3'}),
        (['foo=bar', 'foo=baz', 'foo=zap'], {'foo': ['bar', 'baz', 'zap']}),
    ]
    for attrs, parsed in attributes:
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
    ]
    for attrs in attributes:
        with pytest.raises(click.ClickException):
            kernelci.cli.split_attributes(attrs)


def test_split_attributes_request():
    """Test the generated URL with parameters from split attributes"""
    attributes = [
        (['x=y'], '/?x=y'),
        (['x >= 2'], '/?x__gte=2'),
        (['x >= 2', 'x != 3'], '/?x__gte=2&x__ne=3'),
        (['x >= 2', 'y < 5'], '/?x__gte=2&y__lt=5'),
        (['name=bob', 'name=alice'], '/?name=bob&name=alice'),
    ]
    for attrs, path in attributes:
        params = kernelci.cli.split_attributes(attrs)
        req = requests.Request('GET', 'http://a.b', params=params)
        prepared = req.prepare()
        assert prepared.path_url == path


def test_pagination():
    """Test the logic to get pagination values"""
    values = {
        (None, None): (0, 10),
        (1, 0): (0, 1),
        (1, 1): (1, 1),
        (12, 345): (12 * 345, 12),
        (12345, 3): (3 * 12345, 12345),
        (4567, 0): (0, 4567),
    }
    for (p_len, p_num), (offset, limit) in values.items():
        result = kernelci.cli.get_pagination(p_len, p_num)
        assert result == (offset, limit)


def test_invalid_pagination():
    """Test that errors are reported with invalid pagination values"""
    values = [
        (0, 1),
        (0.1, 1),
        (-1, 0),
        (0, 0),
        (0, -1),
        (1, -1),
        (-123, -123),
        (123, -1),
        (0, 123),
    ]
    for p_len, p_num in values:
        with pytest.raises(click.UsageError):
            kernelci.cli.get_pagination(p_len, p_num)
