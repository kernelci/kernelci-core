# Copyright (C) 2019, 2020, 2021 Collabora Limited
# Author: Lakshmipathi G <lakshmipathi.ganapathi@collabora.com>
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

from kernelci import shell_cmd
from kernelci.storage import upload_files
import os


class RootfsBuilder:

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def build(self, config, data_path, arch):
        raise NotImplementedError("build() needs to be implemented")


class DebosBuilder(RootfsBuilder):

    def build(self, config, data_path, arch):
        debos_params = {
            'architecture': arch,
            'suite': config.debian_release,
            'basename': '/'.join([self.name, arch]),
            'extra_packages': ' '.join(config.extra_packages),
            'extra_packages_remove': ' '.join(config.extra_packages_remove),
            'extra_files_remove':  ' '.join(config.extra_files_remove),
            'extra_firmware': ' '.join(config.extra_firmware),
            'script': config.script,
            'test_overlay': config.test_overlay,
            'crush_image_options': ' '.join(config.crush_image_options),
            'debian_mirror': config.debian_mirror,
            'keyring_package': config.keyring_package,
            'keyring_file': config.keyring_file,
        }
        debos_opts = ' '.join(
            opt for opt in (
                '-t {key}:"{value}"'.format(key=key, value=value)
                for key, value in debos_params.items()
            )
        )
        cmd = "cd {path} && debos --memory=4G {opts} rootfs.yaml".format(
            path=data_path, opts=debos_opts
        )
        return shell_cmd(cmd, True)


class BuildrootBuilder(RootfsBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frag = 'baseline'  # ToDo: add to configuration

    def build(self, config, data_path, arch):
        cmd = 'cd {data_path} && ./configs/frags/build {arch} {frag}'.format(
            data_path=data_path,
            arch=arch,
            frag=self._frag
        )
        return shell_cmd(cmd, True)


class ChromiumosBuilder(RootfsBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frag = 'baseline'  # ToDo: add to configuration

    def build(self, config, data_path, arch):
        cmd = 'cd {data_path} && ./scripts/build_board.sh \
              {board} {branch}'.format(
            data_path=data_path,
            board=config.board,
            branch=config.branch
        )
        return shell_cmd(cmd, True)


ROOTFS_BUILDERS = {
    'debos': DebosBuilder,
    'buildroot': BuildrootBuilder,
    'chromiumos': ChromiumosBuilder,
}


def build(name, config, data_path, arch):
    """Build rootfs images.

    *name* is the rootfs config
    *config* contains rootfs-configs.yaml entries
    *data_path* points to debos or buildroot location
    *arch* required architecture
    """
    builder_cls = ROOTFS_BUILDERS.get(config.rootfs_type)
    if builder_cls is None:
        raise ValueError("rootfs_type not supported: {}".format(
            config.rootfs_type))

    builder = builder_cls(name)
    return builder.build(config, data_path, arch)


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
