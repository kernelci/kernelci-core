#!/usr/bin/env python3
#
# Copyright (C) 2020 Collabora Limited
# Author: Michal Galka <michal.galka@collabora.com>
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from kernelci.legacy.cli import Args, Command, parse_opts  # noqa: E402
import kernelci.build  # noqa: E402
import kernelci.legacy.config.db  # noqa: E402
import kernelci.db  # noqa: E402


class cmd_validate(Command):
    help = "Validate the YAML configuration"
    opt_args = [Args.verbose]

    def __call__(self, configs, args):
        # ToDo: Use jsonschema

        entries = [
            'db_configs',
        ]
        err = kernelci.config.validate_yaml(args.yaml_config, entries)
        if err:
            print(err)
            return False

        return True


class cmd_list_configs(Command):
    help = "List all database configurations"

    def __call__(self, config_data, args):
        db_configs = config_data['db_configs']
        for config_name in db_configs:
            print(config_name)
        return True


class cmd_submit(Command):
    help = "Submit data to the specified database"
    args = [Args.db_config, Args.data_file]
    opt_args = [Args.db_token, Args.verbose]

    def __call__(self, config_data, args):
        config = config_data['db_configs'][args.db_config]
        if args.data_file == '-':
            data = sys.stdin.read()
        else:
            with open(args.data_file, 'r') as json_file:
                data = json.load(json_file)
        db = kernelci.db.get_db(config, args.db_token)
        return db.submit(data, args.verbose)


class cmd_submit_build(Command):
    help = "Submit meta-data for a kernel build"
    args = [Args.kdir, Args.db_config]
    opt_args = [Args.db_token, Args.output, Args.verbose]

    def __call__(self, config_data, args):
        config = config_data['db_configs'][args.db_config]
        install = kernelci.build.Step.get_install_path(args.kdir, args.output)
        meta = kernelci.build.Metadata(install)
        db = kernelci.db.get_db(config, args.db_token)
        return db.submit_build(meta, args.verbose)


class cmd_submit_test(Command):
    help = "Submit test results"
    args = [Args.db_config, Args.data_file]
    opt_args = [Args.db_token, Args.verbose]

    def __call__(self, config_data, args):
        config = config_data['db_configs'][args.db_config]
        with open(args.data_file, 'r') as json_file:
            data = json.load(json_file)
        db = kernelci.db.get_db(config, args.db_token)
        return db.submit_test(data, args.verbose)


class cmd_create_user(Command):
    help = "Create new user"
    args = [Args.db_config, Args.username, Args.password]
    opt_args = [Args.is_admin, Args.db_token, Args.verbose]

    def __call__(self, config_data, args):
        config = config_data['db_configs'][args.db_config]
        db = kernelci.db.get_db(config, args.db_token)
        resp = db.create_user(
            args.username, args.password, args.is_admin, args.verbose
        )
        if args.verbose:
            print(resp)
        return resp


def main():
    opts = parse_opts("kci_data", globals())
    configs = kernelci.config.load(opts.get_yaml_configs())
    status = opts.command(configs, opts)
    sys.exit(0 if status is True else 1)


if __name__ == '__main__':
    main()
