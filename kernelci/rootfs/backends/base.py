# SPDX-License-Identifier: LGPL-2.1-or-later
"""Common interface for rootfs build backends."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..artifacts import ArtifactPaths
from ..config import RootfsConfig
from ..runner import ContainerRunner


@dataclass(frozen=True)
class BuildContext:
    """Resolved inputs for one rootfs configuration and architecture."""

    name: str
    arch: str
    config: RootfsConfig
    data_dir: Path
    paths: ArtifactPaths
    image: str
    runner: ContainerRunner


class RootfsBackend(Protocol):
    """Interface implemented by each rootfs build backend."""

    rootfs_type: str

    def build(self, context: BuildContext) -> None:
        """Build one rootfs variant into ``context.paths.staging``."""
