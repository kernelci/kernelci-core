#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI command line utilities

This module provides base features for KernelCI command line tools.  Based on
the Click framework, it adds support for loading default values and secrets
from TOML settings.
"""

import click

import kernelci.settings


class Args:  # pylint: disable=too-few-public-methods
    """Common command line arguments"""
    api = click.option(
        '--api',
        help="Name of the API config entry"
    )
    config = click.option(
        '-c', '--yaml-config', 'config',
        help="Path to the YAML pipeline configuration"
    )
    indent = click.option(
        '--indent', type=int,
        help="Intentation level for structured data output"
    )
    settings = click.option(
        '-s', '--toml-settings', 'settings',
        help="Path to the TOML user settings"
    )
    verbose = click.option(
        '-v', '--verbose/--no-verbose', default=None,
        help="Print more details output"
    )


class CommandSettings:
    """Settings object passed to commands via the context"""

    def __init__(self, settings_path):
        self._settings = kernelci.settings.Settings(settings_path)

    def __getattr__(self, *args):
        """Get a settings value for the current command group"""
        return self.get(*args)

    @property
    def settings(self):
        """TOML Settings object"""
        return self._settings

    @property
    def secrets(self):
        """Secrets loaded from TOML settings"""
        return self._secrets

    def get(self, *args):
        """Get a settings value like __getattr__()"""
        return self._settings.get(*args)

    def get_secrets(self, params, root):
        """Get a Secrets object with the secrets loaded from the settings"""
        return kernelci.settings.Secrets(self._settings, params, root)


class Kci(click.Command):
    """Wrapper command to load settings and populate default values"""

    def __init__(self, *args, kci_secrets: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._kci_secrets = kci_secrets

    def _walk_name(self, ctx):
        name = (ctx.info_name,)
        if ctx.parent:
            return self._walk_name(ctx.parent) + name
        return name

    def invoke(self, ctx):
        path = self._walk_name(ctx)
        for key, value in ctx.params.items():
            if value is None:
                ctx.params[key] = ctx.obj.get(*path, key)
        if self._kci_secrets:
            root = (path[0], 'secrets')
            ctx.params['secrets'] = ctx.obj.get_secrets(ctx.params, root)
        super().invoke(ctx)


class KciS(Kci):
    """Wrapper command with `secrets` as additional function argument"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, kci_secrets=True, **kwargs)


# pylint: disable=not-callable
class KciGroup(click.core.Group):
    """Click group to create commands with Kci or KciS classes"""

    def command(self, *args, cls=Kci, secrets=False, **kwargs):
        """Wrapper for the command decorator to use Kci or KciS

        If secrets is set to True, the class used for the command is always
        KciS.  Otherwise, Kci is used by default.
        """
        kwargs['cls'] = KciS if secrets is True else cls
        decorator = super().command(**kwargs)
        return decorator if not args else decorator(args[0])

    def group(self, *args, cls=None, **kwargs):
        """Wrapper to use KciGroup for sub-groups"""
        kwargs['cls'] = cls or self.__class__
        decorator = super().group(**kwargs)
        return decorator if not args else decorator(args[0])


@click.group(cls=KciGroup)
@Args.settings
@click.pass_context
def kci(ctx, settings):
    """Entry point for the kci command line tool"""
    ctx.obj = CommandSettings(settings)
