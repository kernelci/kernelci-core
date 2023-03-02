# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API"""

import importlib


def get_api(config, token=None):
    """Get a KernelCI API object matching the provided configuration"""
    mod = importlib.import_module('.'.join(['kernelci', 'db', 'kernelci_api']))
    api = mod.get_db(config, token)
    return api
