# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for typed rootfs builder configuration."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from kernelci.rootfs.config import (
    BuildrootRootfsConfig,
    DebosRootfsConfig,
    RootfsConfigError,
    load_rootfs_config,
    validate_debos_assets,
)

CONFIG_PATH = Path("config/core/rootfs-configs.yaml")
DATA_PATH = Path("config/rootfs").resolve()


def write_config(tmp_path, rootfs_configs):
    path = tmp_path / "rootfs.yaml"
    path.write_text(
        yaml.safe_dump({"rootfs_configs": rootfs_configs}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_load_canonical_config():
    config = load_rootfs_config(CONFIG_PATH)

    assert len(config.rootfs_configs) == 19
    assert isinstance(
        config.rootfs_configs["buildroot-baseline"], BuildrootRootfsConfig
    )
    assert isinstance(config.rootfs_configs["trixie"], DebosRootfsConfig)
    validate_debos_assets(config, DATA_PATH)


def test_reject_unknown_backend(tmp_path):
    path = write_config(
        tmp_path,
        {"example": {"rootfs_type": "unknown", "arch_list": ["x86"]}},
    )

    with pytest.raises(ValidationError, match="union_tag_invalid"):
        load_rootfs_config(path)


def test_reject_unknown_field(tmp_path):
    path = write_config(
        tmp_path,
        {
            "example": {
                "rootfs_type": "debos",
                "debian_release": "trixie",
                "arch_list": ["amd64"],
                "typo": True,
            }
        },
    )

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        load_rootfs_config(path)


@pytest.mark.parametrize("arch_list", [["x86", "arm64"], ["x86", "x86"]])
def test_reject_invalid_architectures(tmp_path, arch_list):
    path = write_config(
        tmp_path,
        {
            "example": {
                "rootfs_type": "buildroot",
                "git_url": "https://example.com/buildroot",
                "git_branch": "main",
                "arch_list": arch_list,
                "frags": ["baseline"],
            }
        },
    )

    with pytest.raises(ValidationError, match="arch_list"):
        load_rootfs_config(path)


def test_reject_missing_buildroot_fragments(tmp_path):
    path = write_config(
        tmp_path,
        {
            "example": {
                "rootfs_type": "buildroot",
                "git_url": "https://example.com/buildroot",
                "git_branch": "main",
                "arch_list": ["x86"],
                "frags": [],
            }
        },
    )

    with pytest.raises(ValidationError, match="frags"):
        load_rootfs_config(path)


def test_reject_debos_asset_outside_data_dir(tmp_path):
    data_dir = tmp_path / "rootfs"
    debos_dir = data_dir / "debos"
    debos_dir.mkdir(parents=True)
    (debos_dir / "rootfs.yaml").write_text("actions: []\n", encoding="utf-8")
    path = write_config(
        tmp_path,
        {
            "example": {
                "rootfs_type": "debos",
                "debian_release": "trixie",
                "arch_list": ["amd64"],
                "script": "../../outside.sh",
            }
        },
    )

    with pytest.raises(RootfsConfigError, match="escapes"):
        validate_debos_assets(load_rootfs_config(path), data_dir)
