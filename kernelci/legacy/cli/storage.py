# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to interact with storage services supported by KernelCI"""

import os.path

import kernelci.storage
from .base import Args, Command, sub_main


class cmd_upload(Command):  # pylint: disable=invalid-name
    """Upload files to storage"""

    args = Command.args + [
        Args.storage_config,
        {
            'name': 'files',
            'nargs': '+',
            'help': "Files to upload",
        },
    ]
    opt_args = Command.opt_args + [
        Args.storage_cred,
        Args.upload_path,
    ]

    def __call__(self, configs, args):
        storage_config = configs['storage_configs'].get(args.storage_config)
        storage = kernelci.storage.get_storage(
            storage_config, args.storage_cred
        )
        for file_path in args.files:
            url = storage.upload_single(
                (file_path, os.path.basename(file_path)),
                args.upload_path or ''
            )
            print(url)


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("storage", globals(), args)
