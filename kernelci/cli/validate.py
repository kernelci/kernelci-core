# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import sys

from .base import Args, Command, parse_opts, sub_main
import kernelci.config


class cmd_yaml(Command):
    help = "Validate the YAML configuration"
    opt_args = [Args.verbose]

    def __call__(self, configs, args):
        entries = [
            'device_types',
            'test_plans',
            'storage_configs',
        ]
        err = kernelci.config.validate_yaml(args.yaml_config, entries)
        if err:
            print(err)
            return False
        if args.verbose:
            print("YAML configuration validation completed.")
        return True


def main(args=None):
    sub_main("validate", globals(), args)
