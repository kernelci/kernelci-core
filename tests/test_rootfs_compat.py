# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for the deprecated kci_rootfs compatibility wrapper."""

from unittest import mock

import pytest

from kernelci.scripts import kci_rootfs


@mock.patch("kernelci.scripts.kci_rootfs.kci.main")
def test_legacy_build_maps_output_layout(kci_main, capsys):
    kci_rootfs.main(
        [
            "--yaml-config",
            "config/core/rootfs-configs.yaml",
            "build",
            "--rootfs-config",
            "trixie",
            "--arch",
            "amd64",
            "--output",
            "/tmp/output",
            "--data-path",
            "config/rootfs/debos",
        ]
    )

    command = kci_main.call_args.kwargs["args"]
    assert command[:5] == [
        "rootfs",
        "build",
        "trixie",
        "--arch",
        "amd64",
    ]
    assert command[command.index("--output-dir") + 1] == "/tmp/output/_install_"
    assert command[command.index("--data-dir") + 1] == "config/rootfs"
    assert "deprecated" in capsys.readouterr().err


def test_legacy_list_variants_uses_typed_configuration(capsys):
    kci_rootfs.main(
        [
            "--yaml-config",
            "config/core/rootfs-configs.yaml",
            "list_variants",
            "--rootfs-config",
            "buildroot-baseline",
            "--arch",
            "x86",
        ]
    )

    output = capsys.readouterr().out
    assert output == "buildroot-baseline x86 buildroot\n"


def test_legacy_upload_reports_migration(capsys):
    with pytest.raises(SystemExit, match="publication belongs"):
        kci_rootfs.main(["upload"])
    assert "deprecated" in capsys.readouterr().err
