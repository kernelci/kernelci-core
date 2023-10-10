# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Unit test for the KernelCI command line tools"""

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
