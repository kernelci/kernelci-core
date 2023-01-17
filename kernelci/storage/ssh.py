# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI storage implementation for SSH"""

import os
import kernelci
from . import Storage


class StorageSSH(Storage):
    """Storage implementation for SSH

    This class implements the Storage interface for uploading files using SSH.
    It requires the path to an SSH private key (identity) as credentials.
    """

    def _upload(self, file_paths, dest_path):
        for src, dst in file_paths:
            dst_file = os.path.join(self.config.path, dest_path, dst)
            dst_dir = os.path.dirname(dst_file)
            kernelci.shell_cmd("""\
ssh \
  -i {key} \
  -p {port} \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  {user}@{host} \
  mkdir -p {dst_dir} && \
scp \
  -i {key} \
  -P {port} \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  {src} \
  {user}@{host}:{dst_file}
""".format(host=self.config.host, port=self.config.port,  # noqa
           key=self.credentials, user=self.config.user,
           src=src, dst_dir=dst_dir, dst_file=dst_file))


def get_storage(config, credentials):
    """Get a Storage_ssh object"""
    return StorageSSH(config, credentials)
