# Copyright (C) 2022 Collabora Limited
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

import os
import kernelci
from . import Storage


class Storage_ssh(Storage):
    """Storage implementation for SSH

    This class implements the Storage interface for uploading files using SSH.
    It requires the path to an SSH private key (identity) as credentials.
    """

    def _upload(self, file_paths, dest_path):
        cmd = """\
scp \
  -i {key} \
  -P {port} \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  {src} \
  {user}@{host}:{dst}
""".format(host=self.config.host, port=self.config.port,
           key=self.credentials, user=self.config.user,
           src=' '.join(file_paths),
           dst=os.path.join(self.config.path, dest_path))
        kernelci.shell_cmd(cmd)


def get_storage(config, credentials):
    """Get a Storage_ssh object"""
    return Storage_ssh(config, credentials)
