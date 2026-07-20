# SPDX-License-Identifier: LGPL-2.1-or-later
"""High-level rootfs build orchestration."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Type

from .artifacts import ArtifactManager
from .backends.base import BuildContext, RootfsBackend
from .backends.buildroot import BuildrootBackend
from .backends.debos import DebosBackend
from .config import (
    BuildrootRootfsConfig,
    RootfsConfigFile,
    validate_debos_assets,
)
from .runner import ContainerRunner

DEFAULT_IMAGES = {
    "debos": "ghcr.io/kernelci/debos:kernelci",
    "buildroot": "ghcr.io/kernelci/buildroot:kernelci",
}

BACKENDS: Dict[str, Type[RootfsBackend]] = {
    "debos": DebosBackend,
    "buildroot": BuildrootBackend,
}


class RootfsBuildError(RuntimeError):
    """Raised for invalid requests or failed rootfs builds."""


class RootfsBuilder:
    """Build validated configurations through registered backends."""

    def __init__(
        self,
        configs: RootfsConfigFile,
        data_dir: Path,
        output_dir: Path,
        cache_dir: Path,
        runner: ContainerRunner,
        images: Optional[Dict[str, str]] = None,
        keep_failed: bool = False,
    ):
        self.configs = configs
        self.data_dir = data_dir.resolve()
        self.artifacts = ArtifactManager(output_dir, cache_dir)
        self.runner = runner
        self.images = dict(DEFAULT_IMAGES)
        self.images.update(images or {})
        self.keep_failed = keep_failed
        validate_debos_assets(configs, self.data_dir)

    def build(self, name: str, arch: str) -> Path:
        """Build one named configuration and return its artifact directory."""
        config = self.configs.rootfs_configs.get(name)
        if config is None:
            known = ", ".join(self.configs.rootfs_configs)
            raise RootfsBuildError(
                f"unknown rootfs configuration '{name}'; known: {known}"
            )
        if arch not in config.arch_list:
            supported = ", ".join(config.arch_list)
            raise RootfsBuildError(
                f"architecture '{arch}' is not supported by {name}; "
                f"supported: {supported}"
            )

        backend_class = BACKENDS.get(config.rootfs_type)
        if backend_class is None:
            raise RootfsBuildError(
                f"no backend registered for {config.rootfs_type}"
            )
        image = self.images[config.rootfs_type]
        paths = self.artifacts.prepare(name, arch, config.rootfs_type)
        context = BuildContext(
            name=name,
            arch=arch,
            config=config,
            data_dir=self.data_dir,
            paths=paths,
            image=image,
            runner=self.runner,
        )
        started = datetime.now(timezone.utc)
        try:
            backend_class().build(context)
            self._write_manifest(context, started)
            self.artifacts.publish(paths)
        except Exception:
            self.artifacts.discard(paths, self.keep_failed)
            raise
        return paths.final

    def _write_manifest(
        self, context: BuildContext, started: datetime
    ) -> None:
        artifact_data = []
        for path in sorted(context.paths.staging.iterdir()):
            if not path.is_file():
                continue
            artifact_data.append(
                {
                    "name": path.name,
                    "size": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
        manifest = {
            "schema_version": 1,
            "name": context.name,
            "backend": context.config.rootfs_type,
            "architecture": context.arch,
            "core_revision": _git_revision(self.data_dir),
            "source_revision": _source_revision(context),
            "builder_image": self.runner.image_identity(context.image),
            "configuration": context.config.model_dump(mode="json"),
            "started": started.isoformat(),
            "finished": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifact_data,
        }
        output = context.paths.staging / "rootfs-build.json"
        output.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision(path: Path) -> Optional[str]:
    result = subprocess.run(
        ("git", "-C", str(path), "rev-parse", "HEAD"),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _source_revision(context: BuildContext) -> Optional[str]:
    if not isinstance(context.config, BuildrootRootfsConfig):
        return None
    return _git_revision(context.paths.work / "buildroot")
