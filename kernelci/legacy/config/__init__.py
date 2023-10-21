# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited

import glob
import os
import yaml

from . import (
    build as build_config,
    db as db_config,
    rootfs as rootfs_config,
    test as test_config,
)


def from_yaml(data, filters):
    """Load legacy YAML configuration data"""
    config = dict()
    config.update(build_config.from_yaml(data, filters))
    config.update(db_config.from_yaml(data, filters))
    config.update(rootfs_config.from_yaml(data, filters))
    config.update(test_config.from_yaml(data, filters))
    return config
