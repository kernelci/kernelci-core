# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>

"""KernelCI storage implementation for SSH"""

import os

from paramiko import client, SSHClient
from scp import SCPClient

from . import Storage


class StorageSSH(Storage):
    """Storage implementation for SSH

    This class implements the Storage interface for uploading files using SSH.
    It requires the path to an SSH private key (identity) as credentials.
    """

    def _upload(self, file_paths, dest_path):
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(client.AutoAddPolicy)
            ssh.connect(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.user,
                key_filename=self.credentials,
                timeout=5000
            )
            with SCPClient(ssh.get_transport()) as scp:
                for src, dst in file_paths:
                    dst_file = os.path.join(self.config.path, dest_path, dst)
                    dst_dir = os.path.dirname(dst_file)
                    ssh.exec_command(f'mkdir -p {dst_dir}')
                    scp.put(src, dst_file)


def get_storage(config, credentials):
    """Get a Storage_ssh object"""
    return StorageSSH(config, credentials)
