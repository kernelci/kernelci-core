# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
#
# NOTE: Deprecated as of move to kernelci-api usermanager.
# Final removal date: 2026-02-02.

"""Deprecated user management commands (moved to kernelci-api usermanager)"""

import click

from . import kci


@kci.group(name='user', invoke_without_command=True)
@click.pass_context
def kci_user(ctx):
    """Deprecated user management group"""
    if ctx.invoked_subcommand is None:
        click.echo(
            "kci user has been deprecated; use kernelci-api usermanager instead."
        )


@kci_user.command
def deprecated():
    """Deprecated: use kernelci-api usermanager instead"""
    click.echo(
        "kci user has been deprecated; use kernelci-api usermanager instead."
    )
