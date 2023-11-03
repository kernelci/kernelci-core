# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to run generic queries with KernelCI API instances"""

import json

import click

import kernelci.api
import kernelci.config
from . import Args, kci


@kci.group(name='api')
def kci_api():
    """Run generic queries with API instances"""


@kci_api.command
@Args.config
@Args.api
@Args.indent
def hello(config, indent, api):
    """Query the API root endpoint"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config)
    data = api.hello()
    click.echo(json.dumps(data, indent=indent or None))
