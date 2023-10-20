# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to manage KernelCI API users"""

import json

import click

import kernelci.api
import kernelci.config
from . import Args, kci


@kci.group(name='user')
def kci_user():
    """Manage user accounts"""


@kci_user.command(secrets=True)
@Args.config
@Args.api
@Args.indent
def whoami(config, api, indent, secrets):
    """Use whoami to get current user info with API authentication"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    data = api.whoami()
    click.echo(json.dumps(data, indent=indent))
