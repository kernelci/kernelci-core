# SPDX-License-Identifier: LGPL-2.1-or-later
"""Typed configuration for root filesystem image builds."""

from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_CONFIG_PATHS = (
    Path("config/core/rootfs-configs.yaml"),
    Path("/etc/kernelci/core/rootfs-configs.yaml"),
)
DEFAULT_DATA_PATHS = (
    Path("config/rootfs"),
    Path("/etc/kernelci/rootfs"),
)


class RootfsConfigError(ValueError):
    """Raised when rootfs configuration or its assets are invalid."""


class BaseRootfsConfig(BaseModel):
    """Fields shared by every supported rootfs backend."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    arch_list: List[str] = Field(min_length=1)

    @field_validator("arch_list")
    @classmethod
    def validate_arch_list(cls, value: List[str]) -> List[str]:
        if len(value) != len(set(value)):
            raise ValueError("arch_list contains duplicate entries")
        if value != sorted(value):
            raise ValueError("arch_list must be sorted")
        return value


class DebosRootfsConfig(BaseRootfsConfig):
    """Configuration accepted by the Debos backend."""

    rootfs_type: Literal["debos"]
    debian_release: str
    extra_packages: List[str] = Field(default_factory=list)
    extra_packages_remove: List[str] = Field(default_factory=list)
    extra_files_remove: List[str] = Field(default_factory=list)
    extra_firmware: List[str] = Field(default_factory=list)
    linux_fw_version: str = ""
    script: str = ""
    test_overlay: str = ""
    crush_image_options: List[str] = Field(default_factory=list)
    debian_mirror: str = ""
    keyring_package: str = ""
    keyring_file: str = ""
    imagesize: str = ""
    debos_memory: str = ""
    debos_cpus: str = ""
    debos_scratchsize: str = ""


class BuildrootRootfsConfig(BaseRootfsConfig):
    """Configuration accepted by the Buildroot backend."""

    rootfs_type: Literal["buildroot"]
    git_url: str = Field(min_length=1)
    git_branch: str = Field(min_length=1)
    frags: List[str] = Field(min_length=1)

    @field_validator("frags")
    @classmethod
    def validate_fragments(cls, value: List[str]) -> List[str]:
        if len(value) != len(set(value)):
            raise ValueError("frags contains duplicate entries")
        if value != sorted(value):
            raise ValueError("frags must be sorted")
        return value


RootfsConfig = Annotated[
    Union[DebosRootfsConfig, BuildrootRootfsConfig],
    Field(discriminator="rootfs_type"),
]


class RootfsConfigFile(BaseModel):
    """Top-level contents of ``rootfs-configs.yaml``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rootfs_configs: Dict[str, RootfsConfig]

    @field_validator("rootfs_configs")
    @classmethod
    def validate_names(
        cls, value: Dict[str, RootfsConfig]
    ) -> Dict[str, RootfsConfig]:
        if not value:
            raise ValueError("rootfs_configs must not be empty")
        if list(value) != sorted(value):
            raise ValueError("rootfs_configs must be sorted")
        return value


def find_default_path(candidates, description: str) -> Path:
    """Return the first existing path from *candidates*."""
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates)
    raise RootfsConfigError(f"{description} not found; searched: {searched}")


def load_rootfs_config(
    config_path: Optional[Union[str, Path]] = None,
) -> RootfsConfigFile:
    """Load and validate the canonical rootfs configuration file."""
    path = (
        Path(config_path).expanduser().resolve()
        if config_path
        else find_default_path(DEFAULT_CONFIG_PATHS, "rootfs configuration")
    )
    if not path.is_file():
        raise RootfsConfigError(f"rootfs configuration is not a file: {path}")
    try:
        with path.open(encoding="utf-8") as config_file:
            data = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        raise RootfsConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RootfsConfigError(f"rootfs configuration must be a mapping: {path}")
    return RootfsConfigFile.model_validate(data)


def find_rootfs_data_dir(
    data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve the directory containing backend recipes and assets."""
    path = (
        Path(data_dir).expanduser().resolve()
        if data_dir
        else find_default_path(DEFAULT_DATA_PATHS, "rootfs data directory")
    )
    if not path.is_dir():
        raise RootfsConfigError(f"rootfs data path is not a directory: {path}")
    return path


def validate_debos_assets(config: RootfsConfigFile, data_dir: Path) -> None:
    """Validate configured Debos scripts and overlays against *data_dir*."""
    debos_dir = (data_dir / "debos").resolve()
    recipe = debos_dir / "rootfs.yaml"
    if not recipe.is_file():
        raise RootfsConfigError(f"Debos recipe not found: {recipe}")

    for name, rootfs in config.rootfs_configs.items():
        if not isinstance(rootfs, DebosRootfsConfig):
            continue
        for field_name in ("script", "test_overlay"):
            relative = getattr(rootfs, field_name)
            if not relative:
                continue
            candidate = (debos_dir / relative).resolve()
            try:
                candidate.relative_to(debos_dir)
            except ValueError as exc:
                raise RootfsConfigError(
                    f"{name}.{field_name} escapes the Debos data directory"
                ) from exc
            if not candidate.exists():
                raise RootfsConfigError(
                    f"{name}.{field_name} does not exist: {candidate}"
                )
