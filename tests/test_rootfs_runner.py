# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for rootfs container execution and artifact staging."""

import json
import subprocess
from unittest import mock

import pytest

from kernelci.rootfs.artifacts import ArtifactManager
from kernelci.rootfs.runner import ContainerError, ContainerRunner, Mount


def completed(args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_build_container_command(tmp_path):
    source = tmp_path / "source with spaces"
    source.mkdir()
    runner = ContainerRunner(pull="always")

    command = runner.build_command(
        "example/image:tag",
        ("tool", "value;not-shell"),
        mounts=(Mount(source, "/source", read_only=True),),
        workdir="/work",
        user="1000:1000",
        devices=("/dev/kvm",),
        environment={"Z": "last", "A": "first"},
    )

    assert command[:6] == ["docker", "run", "--rm", "--pull", "always", "--mount"]
    assert f"source={source.resolve()}" in command[6]
    assert "readonly" in command[6]
    assert command[-3:] == ["example/image:tag", "tool", "value;not-shell"]
    assert ["--env", "A=first"] == command[9:11]


@mock.patch("subprocess.run")
def test_runner_propagates_command_failure(run):
    run.return_value = completed([], returncode=7, stderr="failed")
    runner = ContainerRunner()

    with pytest.raises(ContainerError, match="exit code 7: failed"):
        runner.run("image", ("false",))


@mock.patch("subprocess.run")
def test_normalize_ownership_uses_container(run, tmp_path):
    run.return_value = completed([])
    runner = ContainerRunner()

    runner.normalize_ownership("image", tmp_path)

    command = run.call_args.args[0]
    assert command[:5] == ["docker", "run", "--rm", "--pull", "never"]
    assert command[-4] == "image"
    assert command[-3] == "-R"
    assert command[-1] == "/artifacts"
    assert "--entrypoint" in command


@mock.patch("subprocess.run")
def test_image_identity(run):
    metadata = [{"Id": "sha256:123", "RepoDigests": ["image@sha256:abc"]}]
    run.return_value = completed([], stdout=json.dumps(metadata))

    identity = ContainerRunner().image_identity("image:tag")

    assert identity == {
        "reference": "image:tag",
        "id": "sha256:123",
        "repo_digests": ["image@sha256:abc"],
    }


def test_artifact_publish_replaces_previous_output(tmp_path):
    manager = ArtifactManager(tmp_path / "output", tmp_path / "cache")
    first = manager.prepare("trixie", "amd64", "debos")
    (first.staging / "old").write_text("old", encoding="utf-8")
    manager.publish(first)

    second = manager.prepare("trixie", "amd64", "debos")
    (second.staging / "new").write_text("new", encoding="utf-8")
    manager.publish(second)

    assert not (second.final / "old").exists()
    assert (second.final / "new").read_text(encoding="utf-8") == "new"


def test_failed_staging_does_not_replace_previous_output(tmp_path):
    manager = ArtifactManager(tmp_path / "output", tmp_path / "cache")
    complete = manager.prepare("trixie", "amd64", "debos")
    (complete.staging / "good").touch()
    manager.publish(complete)
    failed = manager.prepare("trixie", "amd64", "debos")
    (failed.staging / "partial").touch()

    manager.discard(failed)

    assert (complete.final / "good").exists()
    assert not failed.staging.exists()


def test_keep_failed_staging(tmp_path):
    manager = ArtifactManager(tmp_path / "output", tmp_path / "cache")
    paths = manager.prepare("trixie", "amd64", "debos")

    manager.discard(paths, keep_failed=True)

    assert paths.staging.is_dir()
