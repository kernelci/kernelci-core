# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to run generic queries with KernelCI API instances"""

from . import (
    Args,
    catch_error,
    echo_json,
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
@catch_error
def hello(config, api, indent):
    """Query the API root endpoint"""
    api = get_api(config, api)
    data = api.hello()
    echo_json(data, indent)
