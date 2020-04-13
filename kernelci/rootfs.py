# Copyright (C) 2019 Collabora Limited
# Author: Lakshmipathi G <lakshmipathi.ganapathi@collabora.com>
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

from kernelci import shell_cmd
from kernelci.storage import upload_files
import os


def _build_debos(name, config, data_path, arch):
    cmd = 'cd {data_path} && debos \
-t architecture:{arch} \
-t suite:{release_name} \
-t basename:{name}/{arch} \
-t extra_packages:"{extra_packages}" \
-t extra_packages_remove:"{extra_packages_remove}" \
-t extra_files_remove:"{extra_files_remove}" \
-t script:"{script}" \
-t test_overlay:"{test_overlay}" \
-t crush_image_options:"{crush_image_options}" \
rootfs.yaml'.format(
            name=name,
            data_path=data_path,
            arch=arch,
            release_name=config.debian_release,
            extra_packages=" ".join(config.extra_packages),
            extra_packages_remove=" ".join(config.extra_packages_remove),
            extra_files_remove=" ".join(config.extra_files_remove),
            script=config.script,
            test_overlay=config.test_overlay,
            crush_image_options=" ".join(config.crush_image_options)
    )
    return shell_cmd(cmd, True)


def build(name, config, data_path, arch):
    """Build rootfs images.

    *name* is the rootfs config
    *config* contains rootfs-configs.yaml entries
    *data_path* points to debos location
    *arch* required architecture
    """
    if config.rootfs_type == "debos":
        return _build_debos(name, config, data_path, arch)
    else:
        raise ValueError("rootfs_type not supported: {}"
                         .format(config.rootfs_type))


def upload(api, token, upload_path, input_dir):
    """Upload rootfs to KernelCI backend.

    *api* is the URL of the KernelCI backend API
    *token* is the backend API token to use
    *upload_path* is the target on KernelCI backend
    *input_dir* is the local rootfs directory path to upload
    """
    artifacts = {}
    for root, _, files in os.walk(input_dir):
        for f in files:
            px = os.path.relpath(root, input_dir)
            artifacts[os.path.join(px, f)] = open(os.path.join(root, f), "rb")
    upload_files(api, token, upload_path, artifacts)
