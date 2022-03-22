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
import shutil


class RootfsBuilder:

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def kci_path(self):
        self_dir = os.path.dirname(__file__)
        absself_dir = os.path.abspath(self_dir)
        kci_path = os.path.split(absself_dir)[0]
        return kci_path

    def build(self, config, data_path, arch, output):
        raise NotImplementedError("build() needs to be implemented")


class DebosBuilder(RootfsBuilder):

    def build(self, config, data_path, arch, output):
        absoutput_dir = os.path.abspath(output)
        artifact_dir = os.path.join(absoutput_dir, '_install_')
        absdata_path = os.path.abspath(data_path)
        rootfs_yaml = os.path.join(absdata_path, 'rootfs.yaml')

        # Create directories if missing
        if not os.path.isdir(artifact_dir):
            os.makedirs(artifact_dir, exist_ok=True)

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
        cmd = f"debos --memory=4G {debos_opts}"\
            f" --artifactdir={artifact_dir} {rootfs_yaml}"\

        print(cmd)
        return shell_cmd(cmd, True)


class BuildrootBuilder(RootfsBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frag = 'baseline'  # ToDo: add to configuration

    def build(self, config, data_path, arch, output):
        absoutput_dir = os.path.abspath(output)
        artifact_dir = os.path.join(absoutput_dir, '_install_',
                                    self.name, arch)
        repo_dir = os.path.join(absoutput_dir, 'buildroot')

        # Hard-coded here for now, should eventually be in YAML config
        git_url = 'https://github.com/kernelci/buildroot'
        git_branch = "main"

        if not os.path.exists(repo_dir):
            shell_cmd(f"""
set -ex
git clone {git_url} {repo_dir}
cd {repo_dir}
git checkout -q origin/{git_branch}
""")
        else:
            shell_cmd(f"""
set -ex
cd {repo_dir}
if [ $(git remote get-url origin) != "{git_url}" ]; then
  git remote set-url origin {git_url}
fi
git remote update origin
git checkout -q origin/{git_branch}
git clean -fd
""")

        shell_cmd(f"""
set -ex
cd {repo_dir}
./configs/frags/build {arch} {self._frag}
""")

        shell_cmd(f"""
set -ex
rm -rf {artifact_dir}
mkdir -p {artifact_dir}
mv {repo_dir}/output/images/* {artifact_dir}
""")

        return True


ROOTFS_BUILDERS = {
    'debos': DebosBuilder,
    'buildroot': BuildrootBuilder,
}


def build(name, config, data_path, arch, output):
    """Build rootfs images.

    *name* is the rootfs config
    *config* contains rootfs-configs.yaml entries
    *arch* required architecture
    *output* artifact output directory
    """
    builder_cls = ROOTFS_BUILDERS.get(config.rootfs_type)
    if builder_cls is None:
        raise ValueError("rootfs_type not supported: {}".format(
            config.rootfs_type))

    builder = builder_cls(name)
    return builder.build(config, data_path, arch, output)


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
