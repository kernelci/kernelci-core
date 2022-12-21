# Copyright (C) 2022 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>
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

import os
from paramiko import client, SSHClient
from scp import SCPClient
from . import Storage


class Storage_ssh(Storage):
    """Storage implementation for SSH

    This class implements the Storage interface for uploading files using SSH.
    It requires the path to an SSH private key (identity) as credentials.
    """

    def _upload(self, file_paths, dest_path):
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(client.AutoAddPolicy)
            ssh.connect(hostname=self.config.host,
                        port=self.config.port,
                        username=self.config.user,
                        key_filename=self.credentials,
                        timeout=5000
                        )
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(file_paths,
                        os.path.join(self.config.path, dest_path))


def get_storage(config, credentials):
    """Get a Storage_ssh object"""
    return Storage_ssh(config, credentials)
