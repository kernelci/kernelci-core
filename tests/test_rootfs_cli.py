# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for the native ``kci rootfs`` command group."""

import json
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from kernelci.cli import kci
from kernelci.cli import rootfs as rootfs_cli  # noqa: F401

CONFIG = "config/core/rootfs-configs.yaml"
DATA = "config/rootfs"


def invoke(*args):
    return CliRunner().invoke(
        kci,
        [
            "rootfs",
            *args,
            "--config",
            CONFIG,
            "--data-dir",
            DATA,
        ],
    )


def test_list_configs_as_json():
    result = invoke("list", "--format", "json")

    assert result.exit_code == 0, result.output
    entries = json.loads(result.output)
    assert entries[0]["name"] == "buildroot-baseline"
    assert entries[0]["type"] == "buildroot"
    assert len(entries) == 19


def test_list_filters_backend():
    result = invoke("list", "--type", "buildroot")

    assert result.exit_code == 0, result.output
    assert result.output == "buildroot-baseline\n"


def test_variants_as_json():
    result = invoke("variants", "buildroot-baseline", "--format", "json")

    assert result.exit_code == 0, result.output
    entries = json.loads(result.output)
    assert entries[0] == {
        "name": "buildroot-baseline",
        "arch": "arc",
        "type": "buildroot",
    }
    assert len(entries) == 8


def test_validate():
    result = invoke("validate")

    assert result.exit_code == 0, result.output
    assert result.output == "Validated 19 rootfs configurations.\n"


def test_build_requires_explicit_arch_selection():
    result = invoke("build", "trixie")

    assert result.exit_code == 2
    assert "either --arch" in result.output


@mock.patch("kernelci.cli.rootfs.RootfsBuilder")
@mock.patch("kernelci.cli.rootfs.ContainerRunner")
def test_build_one_architecture(runner_class, builder_class):
    runner_class.return_value = mock.Mock()
    builder_class.return_value.build.return_value = Path(
        "/tmp/output/trixie/amd64"
    )

    result = invoke("build", "trixie", "--arch", "amd64")

    assert result.exit_code == 0, result.output
    builder_class.return_value.build.assert_called_once_with(
        "trixie", "amd64"
    )
    assert "Artifacts: /tmp/output/trixie/amd64" in result.output


def test_build_rejects_unsupported_architecture():
    result = invoke("build", "buildroot-baseline", "--arch", "amd64")

    assert result.exit_code == 1
    assert "unsupported architecture" in result.output
