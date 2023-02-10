# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to generate and run KernelCI jobs"""

from .base import sub_main


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("job", globals(), args)
