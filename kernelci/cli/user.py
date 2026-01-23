# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
#
"""User management commands"""

from . import Args, catch_error, echo_json, get_api, kci


@kci.group(name='user')
def kci_user():
    """Interact with user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
@catch_error
def whoami(config, api, indent, secrets):
    """Show the current user"""
    api = get_api(config, api, secrets)
    user = api.user.whoami()
    echo_json(user, indent)
