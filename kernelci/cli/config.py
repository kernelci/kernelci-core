# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage the KernelCI YAML configuration"""

import yaml

import kernelci.config
from .base import Args, Command, sub_main


class cmd_list_files(Command):  # pylint: disable=invalid-name
    """List the YAML configuration files"""

    def __call__(self, configs, args):
        paths = kernelci.config.get_config_paths(args.get_yaml_configs())
        for path in paths:
            for yaml_file, _ in kernelci.config.iterate_yaml_files(path):
                print(yaml_file)


class cmd_validate(Command):  # pylint: disable=invalid-name
    """Validate the YAML configuration"""
    opt_args = [Args.verbose]

    def __call__(self, configs, args):
        entries = [
            'api_configs',
            'device_types',
            'jobs',
            'runtimes',
            'storage_configs',
        ]
        err = kernelci.config.validate_yaml(args.yaml_config, entries)
        if err:
            print(err)
            return False
        if args.verbose:
            print("YAML configuration validation completed.")
        return True


class cmd_list(Command):  # pylint: disable=invalid-name
    """List entries from the YAML configuration"""
    args = Command.args + [
        {
            'name': 'config',
            'help': "Name of the YAML config to list, e.g. jobs or runtimes",
        },
    ]
    opt_args = Command.opt_args + [Args.indent]

    def __call__(self, configs, args):
        config_data = configs.get(args.config)
        if not config_data:
            print(f"Configs not found: {args.config}")
            return False
        if isinstance(config_data, dict):
            for name, data in config_data.items():
                print(name)
                print('-' * len(name))
                print(yaml.dump(data, indent=args.indent))
        else:
            for data in config_data:
                print(yaml.dump(data, indent=args.indent))
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("config", globals(), args)
