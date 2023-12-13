# Copyright (C) 2019, 2020, 2021, 2022 Collabora Limited
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

        debos_config = {
            '--cpus':  config.debos_cpus,
            '--memory': config.debos_memory or '4G',
            '--scratchsize': config.debos_scratchsize
        }
        debos_opts = ' '.join([f'{opt}={value}' for opt, value in
                              debos_config.items() if value])

        debos_params = {
            'architecture': arch,
            'suite': config.debian_release,
            'basename': '/'.join([self.name, arch]),
            'extra_packages': ' '.join(config.extra_packages),
            'extra_packages_remove': ' '.join(config.extra_packages_remove),
            'extra_files_remove':  ' '.join(config.extra_files_remove),
            'extra_firmware': ' '.join(config.extra_firmware),
            'linux_fw_version': config.linux_fw_version,
            'script': config.script,
            'test_overlay': config.test_overlay,
            'crush_image_options': ' '.join(config.crush_image_options),
            'debian_mirror': config.debian_mirror,
            'keyring_package': config.keyring_package,
            'keyring_file': config.keyring_file,
            'imagesize': config.imagesize,
        }

        debos_opts += ' ' + ' '.join(
            opt for opt in (
                '-t {key}:"{value}"'.format(key=key, value=value)
                for key, value in debos_params.items()
            )
        )

        cmd = f"debos {debos_opts}"\
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

        if not os.path.exists(repo_dir):
            shell_cmd(f"""
set -ex
git clone {config.git_url} {repo_dir}
cd {repo_dir}
git checkout -q origin/{config.git_branch}
""")
        else:
            shell_cmd(f"""
set -ex
cd {repo_dir}
if [ $(git remote get-url origin) != "{config.git_url}" ]; then
  git remote set-url origin {config.git_url}
fi
git remote update origin
git checkout -q origin/{config.git_branch}
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


class ChromiumosBuilder(RootfsBuilder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build(self, config, data_path, arch, output):
        absoutput_dir = os.path.abspath(output)
        artifact_dir = os.path.join(absoutput_dir, '_install_',
                                    self.name, arch)
        temp_dir = os.path.join(absoutput_dir, 'temp')
        absdata_path = os.path.abspath(data_path)
        build_script = os.path.join(absdata_path,
                                    'scripts', 'build_board.sh')
        # Path to files generated by script
        files_dir = os.path.join(temp_dir, config.board)

        if not os.path.isdir(artifact_dir):
            os.makedirs(artifact_dir, exist_ok=True)
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)

        cmd = f'cd {temp_dir} && {build_script} \
              {config.board} {config.branch} {config.serial}'
        ret = shell_cmd(cmd, True)
        if not ret:
            return False

        cmd = f"sudo mv {files_dir}/* {artifact_dir}"
        return shell_cmd(cmd, True)


ROOTFS_BUILDERS = {
    'debos': DebosBuilder,
    'buildroot': BuildrootBuilder,
    'chromiumos': ChromiumosBuilder,
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


def upload(storage, upload_path, input_dir):
    """Upload rootfs to KernelCI backend.

    *storage* is a Storage object
    *upload_path* is the target on KernelCI backend
    *input_dir* is the local rootfs directory path to upload
    """
    paths = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            src = os.path.join(root, f)
            px = os.path.relpath(root, input_dir)
            dst = os.path.join(px, f)
            paths.append((src, dst))
    storage.upload_multiple(paths, upload_path)
