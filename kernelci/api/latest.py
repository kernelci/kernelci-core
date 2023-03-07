# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI API bindings for the latest version"""

import enum

from . import API


class NodeStates(enum.Enum):
    """Node states names"""
    RUNNING = 'running'
    AVAILABLE = 'available'
    CLOSING = 'closing'
    DONE = 'done'


class LatestAPI(API):
    """Latest API version

    The 'latest' version is used to refer to the current development version,
    so it's not pinned down.  It's a moving target and shouldn't be used in
    production environments.
    """

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def node_states(self):
        return NodeStates

    def hello(self) -> dict:
        return self._get('/').json()

    def whoami(self) -> dict:
        return self._get('/whoami').json()


def get_api(config, token):
    """Get an API object for the latest version"""
    return LatestAPI(config, token)
