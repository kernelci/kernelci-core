# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for the containerized Debos backend."""

import os
from unittest import mock

import pytest

from kernelci.rootfs.artifacts import ArtifactPaths
from kernelci.rootfs.backends.base import BuildContext
from kernelci.rootfs.backends.debos import DebosBackend
from kernelci.rootfs.config import BuildrootRootfsConfig, DebosRootfsConfig


def make_context(tmp_path, config):
    runner = mock.Mock()
    paths = ArtifactPaths(
        final=tmp_path / "final",
        staging=tmp_path / "staging",
        work=tmp_path / "work",
        cache=tmp_path / "cache",
    )
    for path in (paths.staging, paths.work, paths.cache):
        path.mkdir()
    return BuildContext(
        name="trixie",
        arch="arm64",
        config=config,
        data_dir=tmp_path / "data",
        paths=paths,
        image="ghcr.io/kernelci/debos:kernelci",
        runner=runner,
    )


@mock.patch("kernelci.rootfs.backends.debos.Path.exists", return_value=True)
@mock.patch("kernelci.rootfs.backends.debos.Path.stat")
def test_debos_command_and_mounts(path_stat, _path_exists, tmp_path):
    path_stat.return_value.st_gid = 992
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config = DebosRootfsConfig(
        rootfs_type="debos",
        debian_release="trixie",
        arch_list=["arm64"],
        cross_compile=True,
        extra_packages=["curl", "git"],
        extra_packages_remove=["apt"],
        extra_files_remove=["/var/cache"],
        extra_firmware=["iwlwifi"],
        linux_fw_version="20250613",
        script="scripts/setup.sh",
        test_overlay="overlays/test",
        crush_image_options=["--remove-docs"],
        debian_mirror="https://deb.debian.org/debian",
        keyring_package="debian-archive-keyring",
        keyring_file="/usr/share/keyrings/debian.gpg",
        imagesize="2GB",
        debos_memory="8G",
        debos_cpus="4",
        debos_scratchsize="10G",
    )
    context = make_context(tmp_path, config)

    DebosBackend().build(context)

    kwargs = context.runner.run.call_args.kwargs
    command = context.runner.run.call_args.args[1]
    assert command[:4] == [
        "debos",
        "--cpus=4",
        "--memory=8G",
        "--scratchsize=10G",
    ]
    assert "architecture:arm64" in command
    assert "cross_compile:true" in command
    assert "extra_packages:curl git" in command
    assert "basename:." in command
    assert command[-2:] == [
        "--artifactdir=/artifacts",
        "/configs/debos/rootfs.yaml",
    ]
    mounts = {mount.target: mount for mount in kwargs["mounts"]}
    assert mounts["/configs"].read_only
    assert not mounts["/artifacts"].read_only
    assert kwargs["workdir"] == "/work"
    assert kwargs["user"] == f"{os.getuid()}:{os.getgid()}"
    assert kwargs["devices"] == ("/dev/kvm",)
    assert kwargs["groups"] == ("992",)
    context.runner.normalize_ownership.assert_called_once_with(
        context.image, context.paths.staging
    )


@mock.patch("kernelci.rootfs.backends.debos.Path.exists", return_value=False)
def test_debos_defaults_and_omits_empty_variables(_path_exists, tmp_path):
    (tmp_path / "data").mkdir()
    config = DebosRootfsConfig(
        rootfs_type="debos",
        debian_release="trixie",
        arch_list=["arm64"],
    )
    context = make_context(tmp_path, config)

    DebosBackend().build(context)

    command = context.runner.run.call_args.args[1]
    kwargs = context.runner.run.call_args.kwargs
    assert "--memory=4G" in command
    assert "cross_compile:true" not in command
    assert not any(item.startswith("extra_packages:") for item in command)
    assert kwargs["devices"] == ()
    assert kwargs["groups"] == ()


def test_debos_rejects_wrong_config_type(tmp_path):
    config = BuildrootRootfsConfig(
        rootfs_type="buildroot",
        git_url="https://example.com/buildroot",
        git_branch="main",
        arch_list=["arm64"],
        frags=["baseline"],
    )
    context = make_context(tmp_path, config)

    with pytest.raises(TypeError, match="DebosRootfsConfig"):
        DebosBackend().build(context)
