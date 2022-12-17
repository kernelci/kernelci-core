# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI command line utility package"""

import sys

from .base import Args, Command, parse_opts, sub_main
from . import (
    node,
    validate,
)

_COMMANDS = {
    'node': node.main,
    'validate': validate.main,
}


def list_command_names():
    """Return a list with the command names"""
    return list(_COMMANDS.keys())


def call(name, args=None):
    """Call a command registered with kernelci.cli

    Call the command with the given *name* and optional arguments *args*.
    """
    cmd = _COMMANDS.get(name)
    if not cmd:
        print("Unknown command: {name}", file=sys.stderr, flush=True)
        sys.exit(1)
    _COMMANDS[name](args)
