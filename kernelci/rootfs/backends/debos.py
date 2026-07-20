# SPDX-License-Identifier: LGPL-2.1-or-later
"""Debos rootfs build backend."""

from pathlib import Path
from typing import Dict, List

from ..config import DebosRootfsConfig
from ..runner import Mount
from .base import BuildContext


class DebosBackend:
    """Build Debian root filesystems with Debos in a container."""

    rootfs_type = "debos"

    @staticmethod
    def _variables(config: DebosRootfsConfig, arch: str) -> Dict[str, str]:
        def join(name: str) -> str:
            return " ".join(getattr(config, name))

        variables = {
            "architecture": arch,
            "suite": config.debian_release,
            "basename": ".",
            "extra_packages": join("extra_packages"),
            "extra_packages_remove": join("extra_packages_remove"),
            "extra_files_remove": join("extra_files_remove"),
            "extra_firmware": join("extra_firmware"),
            "linux_fw_version": config.linux_fw_version,
            "script": config.script,
            "test_overlay": config.test_overlay,
            "crush_image_options": join("crush_image_options"),
            "debian_mirror": config.debian_mirror,
            "keyring_package": config.keyring_package,
            "keyring_file": config.keyring_file,
            "imagesize": config.imagesize,
        }
        return {key: value for key, value in variables.items() if value}

    def build(self, context: BuildContext) -> None:
        if not isinstance(context.config, DebosRootfsConfig):
            raise TypeError("DebosBackend requires DebosRootfsConfig")

        config = context.config
        command: List[str] = ["debos"]
        if config.debos_cpus:
            command.append(f"--cpus={config.debos_cpus}")
        command.append(f"--memory={config.debos_memory or '4G'}")
        if config.debos_scratchsize:
            command.append(f"--scratchsize={config.debos_scratchsize}")
        for key, value in self._variables(config, context.arch).items():
            command.extend(("-t", f"{key}:{value}"))
        command.extend(
            ("--artifactdir=/artifacts", "/configs/debos/rootfs.yaml")
        )

        mounts = (
            Mount(context.data_dir, "/configs", read_only=True),
            Mount(context.paths.staging, "/artifacts"),
            Mount(context.paths.work, "/work"),
            Mount(context.paths.cache, "/scratch"),
        )
        devices = ("/dev/kvm",) if Path("/dev/kvm").exists() else ()
        context.runner.run(
            context.image,
            command,
            mounts=mounts,
            workdir="/work",
            devices=devices,
            environment={"HOME": "/tmp"},
        )
        context.runner.normalize_ownership(
            context.image, context.paths.staging
        )
