# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to interact with storage services supported by KernelCI"""

import os

import click

import kernelci.config
import kernelci.storage
from . import Args, kci, catch_error


@kci.group(name='storage')
def kci_storage():
    """Interact with KernelCI storage services"""


@kci_storage.command(secrets=True)
@click.argument('filename', type=click.Path(exists=True))
@click.argument('path', required=False)
@Args.config
@Args.storage
@catch_error
def upload(filename, path, config, storage, secrets):
    """Upload FILENAME to the designated storage service in PATH"""
    configs = kernelci.config.load(config)
    storage_config = configs['storage'][storage]
    storage = kernelci.storage.get_storage(
        storage_config, secrets.storage.credentials
    )
    url = storage.upload_single(
        file_path=(filename, os.path.basename(filename)),
        dest_path=(path or '')
    )
    click.echo(url)
