# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for the containerized Buildroot backend."""

from unittest import mock

import pytest

from kernelci.rootfs.artifacts import ArtifactPaths
from kernelci.rootfs.backends.base import BuildContext
from kernelci.rootfs.backends.buildroot import BUILD_SCRIPT, BuildrootBackend
from kernelci.rootfs.config import BuildrootRootfsConfig, DebosRootfsConfig


def make_context(tmp_path, config):
    paths = ArtifactPaths(
        final=tmp_path / "final",
        staging=tmp_path / "staging",
        work=tmp_path / "work",
        cache=tmp_path / "cache",
    )
    for path in (paths.staging, paths.work, paths.cache):
        path.mkdir()
    return BuildContext(
        name="buildroot-baseline",
        arch="x86",
        config=config,
        data_dir=tmp_path / "data",
        paths=paths,
        image="ghcr.io/kernelci/buildroot:kernelci",
        runner=mock.Mock(),
    )


def test_buildroot_command_uses_configured_source_and_fragments(tmp_path):
    config = BuildrootRootfsConfig(
        rootfs_type="buildroot",
        git_url="https://example.com/buildroot;not-shell",
        git_branch="kernelci/test branch",
        arch_list=["x86"],
        frags=["baseline", "debug"],
    )
    context = make_context(tmp_path, config)

    BuildrootBackend().build(context)

    command = context.runner.run.call_args.args[1]
    kwargs = context.runner.run.call_args.kwargs
    assert command[:4] == (
        "bash",
        "-euc",
        BUILD_SCRIPT,
        "kernelci-buildroot",
    )
    assert command[4:] == (
        config.git_url,
        config.git_branch,
        "x86",
        "baseline",
        "debug",
    )
    mounts = {mount.target: mount for mount in kwargs["mounts"]}
    assert set(mounts) == {"/workspace", "/cache", "/artifacts"}
    assert kwargs["environment"]["BR2_DL_DIR"] == "/cache/dl"
    assert kwargs["workdir"] == "/workspace"
    assert ":" in kwargs["user"]


def test_buildroot_script_preserves_cache_and_quotes_arguments():
    assert "git clean -fd\n" in BUILD_SCRIPT
    assert "git clean -fdx" not in BUILD_SCRIPT
    assert './configs/frags/build "$arch" "$@"' in BUILD_SCRIPT
    assert 'git fetch --depth 1 --prune origin "$git_branch"' in BUILD_SCRIPT
    assert "cp -a output/images/. /artifacts/" in BUILD_SCRIPT


def test_buildroot_rejects_wrong_config_type(tmp_path):
    config = DebosRootfsConfig(
        rootfs_type="debos",
        debian_release="trixie",
        arch_list=["x86"],
    )
    context = make_context(tmp_path, config)

    with pytest.raises(TypeError, match="BuildrootRootfsConfig"):
        BuildrootBackend().build(context)
