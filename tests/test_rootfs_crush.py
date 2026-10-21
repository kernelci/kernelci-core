# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run the image cleanup script with package and filesystem commands stubbed."""

import os
import subprocess
from pathlib import Path

import pytest

from kernelci.rootfs.config import load_rootfs_config

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config/rootfs/debos/scripts/crush.sh"


def purged_packages(tmp_path, options):
    """Capture cleanup requests without touching packages or the filesystem."""
    commands = tmp_path / "bin"
    commands.mkdir()
    log = tmp_path / "commands.log"
    for command in ("dpkg", "find", "rm"):
        stub = commands / command
        stub.write_text(
            '#!/bin/sh\nprintf "%s\\n" "${0##*/} $*" >> "$CRUSH_TEST_LOG"\n'
        )
        stub.chmod(0o755)

    subprocess.run(
        ["/bin/sh", str(SCRIPT), *options],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(commands), "CRUSH_TEST_LOG": str(log)},
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line.split()[-1]
        for line in log.read_text().splitlines()
        if line.startswith("dpkg ")
    }


def test_default_cleanup_still_removes_perl(tmp_path):
    """Other rootfs images keep the existing minimal-image behavior."""
    packages = purged_packages(tmp_path, [])

    assert {"perl-base", "cpio", "ncurses-bin", "apt", "dpkg"} <= packages


def test_kselftest_cleanup_keeps_perl_and_runs_default_components(tmp_path):
    """The configured kselftest image keeps its interpreter through cleanup."""
    config = load_rootfs_config(ROOT / "config/core/rootfs-configs.yaml")
    options = config.rootfs_configs["trixie-kselftest"].crush_image_options

    packages = purged_packages(tmp_path, options)

    assert "perl-base" not in packages
    assert {"insserv", "cpio", "ncurses-bin", "apt", "dpkg"} <= packages


@pytest.mark.parametrize(
    "options",
    [["--keep-perl", "misc_packages"], ["misc_packages", "--keep-perl"]],
)
def test_keep_perl_with_explicit_components(tmp_path, options):
    """The flag works in either order without adding cleanup components."""
    packages = purged_packages(tmp_path, options)

    assert "perl-base" not in packages
    assert {"insserv", "passwd"} <= packages
    assert "apt" not in packages
