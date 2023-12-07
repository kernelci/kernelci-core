# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to run generic queries with KernelCI API instances"""

import json

import click

from . import (
    Args,
    get_api,
    kci,
)


@kci.group(name='api')
def kci_api():
    """Run generic queries with API instances"""


@kci_api.command
@Args.config
@Args.api
@Args.indent
def hello(config, api, indent):
    """Query the API root endpoint"""
    api = get_api(config, api)
    data = api.hello()
    click.echo(json.dumps(data, indent=indent or None))
