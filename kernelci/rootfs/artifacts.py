# SPDX-License-Identifier: LGPL-2.1-or-later
"""Staging and publication of rootfs build artifacts."""

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactPaths:
    """Paths allocated for one rootfs build variant."""

    final: Path
    staging: Path
    work: Path
    cache: Path


class ArtifactManager:
    """Keep partial output separate from the last successful build."""

    def __init__(self, output_dir: Path, cache_dir: Path):
        self.output_dir = output_dir.expanduser().resolve()
        self.cache_dir = cache_dir.expanduser().resolve()

    def prepare(self, name: str, arch: str, backend: str) -> ArtifactPaths:
        """Allocate staging, work, and cache paths for a variant."""
        final = self.output_dir / name / arch
        final.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(prefix=f".{name}-{arch}-", dir=final.parent)
        )
        work = self.cache_dir / backend / name / arch / "work"
        cache = self.cache_dir / backend / name / arch / "cache"
        work.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        return ArtifactPaths(final, staging, work, cache)

    @staticmethod
    def publish(paths: ArtifactPaths) -> None:
        """Replace final output with a successfully completed staging tree."""
        backup = paths.final.with_name(f".{paths.final.name}.previous")
        if backup.exists():
            shutil.rmtree(backup)
        if paths.final.exists():
            os.replace(paths.final, backup)
        try:
            os.replace(paths.staging, paths.final)
        except Exception:
            if backup.exists() and not paths.final.exists():
                os.replace(backup, paths.final)
            raise
        if backup.exists():
            shutil.rmtree(backup)

    @staticmethod
    def discard(paths: ArtifactPaths, keep_failed: bool = False) -> None:
        """Remove partial output unless it was requested for debugging."""
        if not keep_failed:
            shutil.rmtree(paths.staging, ignore_errors=True)
