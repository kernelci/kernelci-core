# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for high-level rootfs build orchestration and provenance."""

import json
from unittest import mock

import pytest

from kernelci.rootfs.builder import RootfsBuilder, RootfsBuildError
from kernelci.rootfs.config import RootfsConfigFile


def make_configs():
    return RootfsConfigFile.model_validate(
        {
            "rootfs_configs": {
                "example": {
                    "rootfs_type": "debos",
                    "debian_release": "trixie",
                    "arch_list": ["amd64"],
                }
            }
        }
    )


def make_builder(tmp_path, keep_failed=False):
    data_dir = tmp_path / "data"
    (data_dir / "debos").mkdir(parents=True)
    (data_dir / "debos" / "rootfs.yaml").touch()
    runner = mock.Mock()
    runner.image_identity.return_value = {
        "reference": "debos",
        "id": "sha256:image",
        "repo_digests": ["debos@sha256:digest"],
    }
    builder = RootfsBuilder(
        make_configs(),
        data_dir,
        tmp_path / "output",
        tmp_path / "cache",
        runner,
        images={"debos": "debos"},
        keep_failed=keep_failed,
    )
    return builder, runner


@mock.patch("kernelci.rootfs.builder.BACKENDS")
def test_build_publishes_artifacts_and_manifest(backends, tmp_path):
    backend = mock.Mock()

    def build(context):
        (context.paths.staging / "rootfs.cpio.gz").write_bytes(b"rootfs")

    backend.return_value.build.side_effect = build
    backends.get.return_value = backend
    builder, runner = make_builder(tmp_path)

    output = builder.build("example", "amd64")

    assert output == (tmp_path / "output" / "example" / "amd64").resolve()
    manifest = json.loads((output / "rootfs-build.json").read_text())
    assert manifest["schema_version"] == 1
    assert manifest["name"] == "example"
    assert manifest["architecture"] == "amd64"
    assert manifest["builder_image"]["id"] == "sha256:image"
    assert manifest["artifacts"][0]["name"] == "rootfs.cpio.gz"
    assert len(manifest["artifacts"][0]["sha256"]) == 64
    runner.image_identity.assert_called_once_with("debos")


def test_reject_unknown_configuration(tmp_path):
    builder, _ = make_builder(tmp_path)

    with pytest.raises(RootfsBuildError, match="unknown rootfs"):
        builder.build("missing", "amd64")


def test_reject_unsupported_architecture(tmp_path):
    builder, _ = make_builder(tmp_path)

    with pytest.raises(RootfsBuildError, match="not supported"):
        builder.build("example", "arm64")


@mock.patch("kernelci.rootfs.builder.BACKENDS")
def test_failure_keeps_previous_successful_output(backends, tmp_path):
    backend = mock.Mock()
    backends.get.return_value = backend
    builder, _ = make_builder(tmp_path)

    def succeed(context):
        (context.paths.staging / "good").touch()

    backend.return_value.build.side_effect = succeed
    output = builder.build("example", "amd64")
    backend.return_value.build.side_effect = RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        builder.build("example", "amd64")

    assert (output / "good").exists()
    assert not list(output.parent.glob(".example-amd64-*"))
