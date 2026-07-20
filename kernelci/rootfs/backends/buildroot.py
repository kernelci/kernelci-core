# SPDX-License-Identifier: LGPL-2.1-or-later
"""Buildroot rootfs build backend."""

import os

from ..config import BuildrootRootfsConfig
from ..runner import Mount
from .base import BuildContext

BUILD_SCRIPT = r"""
set -eu
repo_dir=/workspace/buildroot
git_url=$1
git_branch=$2
arch=$3
shift 3

if [ ! -d "$repo_dir/.git" ]; then
    git clone --depth 1 --branch "$git_branch" "$git_url" "$repo_dir"
fi

cd "$repo_dir"
if [ "$(git remote get-url origin)" != "$git_url" ]; then
    git remote set-url origin "$git_url"
fi
git fetch --depth 1 --prune origin "$git_branch"
git checkout --detach FETCH_HEAD
git clean -fd
./configs/frags/build "$arch" "$@"

test -d output/images
find /artifacts -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
cp -a output/images/. /artifacts/
""".strip()


class BuildrootBackend:
    """Build minimal root filesystems from KernelCI Buildroot fragments."""

    rootfs_type = "buildroot"

    def build(self, context: BuildContext) -> None:
        if not isinstance(context.config, BuildrootRootfsConfig):
            raise TypeError(
                "BuildrootBackend requires BuildrootRootfsConfig"
            )

        config = context.config
        command = (
            "bash",
            "-euc",
            BUILD_SCRIPT,
            "kernelci-buildroot",
            config.git_url,
            config.git_branch,
            context.arch,
            *config.frags,
        )
        context.runner.run(
            context.image,
            command,
            mounts=(
                Mount(context.paths.work, "/workspace"),
                Mount(context.paths.cache, "/cache"),
                Mount(context.paths.staging, "/artifacts"),
            ),
            workdir="/workspace",
            user=f"{os.getuid()}:{os.getgid()}",
            environment={"BR2_DL_DIR": "/cache/dl", "HOME": "/tmp"},
        )
