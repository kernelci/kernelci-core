# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for kernelci.kbuild build script generation and metadata"""

import json
import os
import sys
import types
from unittest import mock

import pytest
import requests

from kernelci.kbuild import KBuild


def _kbuild(tmp_path, compiler="clang-21", arch="x86_64"):
    kbuild = object.__new__(KBuild)
    kbuild._af_dir = str(tmp_path / "artifacts")
    kbuild._workspace = str(tmp_path)
    kbuild._srcdir = str(tmp_path / "linux")
    kbuild._arch = arch
    kbuild._compiler = compiler
    kbuild._defconfig = "defconfig"
    kbuild._fragments = []
    kbuild._fragment_files = []
    kbuild._config_full = ""
    kbuild._backend = "tuxmake"
    kbuild._dtbs_check = True
    kbuild._steps = []
    kbuild._artifacts = []
    kbuild._current_job = None
    os.makedirs(kbuild._af_dir)
    return kbuild


def _fake_tuxmake(monkeypatch, compiler_bin):
    fake_pkg = types.ModuleType("tuxmake")
    fake_arch = types.ModuleType("tuxmake.arch")
    fake_toolchain = types.ModuleType("tuxmake.toolchain")

    class Architecture:
        def __init__(self, name):
            self.name = name

    class Toolchain:
        def __init__(self, name):
            self.name = name

        def compiler(self, arch):
            return compiler_bin

    fake_arch.Architecture = Architecture
    fake_toolchain.Toolchain = Toolchain
    monkeypatch.setitem(sys.modules, "tuxmake", fake_pkg)
    monkeypatch.setitem(sys.modules, "tuxmake.arch", fake_arch)
    monkeypatch.setitem(sys.modules, "tuxmake.toolchain", fake_toolchain)


class TestCompilerVersionProbe:
    def test_probe_before_build(self, tmp_path, monkeypatch):
        _fake_tuxmake(monkeypatch, "clang")
        kbuild = _kbuild(tmp_path)
        kbuild._build_with_tuxmake()
        steps = kbuild._steps
        probe = steps.index("clang --version || true")
        build = next(
            i for i, s in enumerate(steps) if "tuxmake --runtime=null" in s
        )
        assert probe < build

    def test_probe_uses_tuxmake_resolution(self, tmp_path, monkeypatch):
        _fake_tuxmake(monkeypatch, "aarch64-linux-gnu-gcc")
        kbuild = _kbuild(tmp_path, compiler="gcc-14", arch="arm64")
        kbuild._build_with_tuxmake()
        assert "aarch64-linux-gnu-gcc --version || true" in kbuild._steps

    def test_probe_clang_fallback_without_tuxmake(self, tmp_path, monkeypatch):
        monkeypatch.setitem(sys.modules, "tuxmake", None)
        kbuild = _kbuild(tmp_path, compiler="clang-21")
        kbuild._build_with_tuxmake()
        assert "clang --version || true" in kbuild._steps

    def test_no_probe_for_gcc_without_tuxmake(self, tmp_path, monkeypatch):
        monkeypatch.setitem(sys.modules, "tuxmake", None)
        kbuild = _kbuild(tmp_path, compiler="gcc-14")
        kbuild._build_with_tuxmake()
        assert not any("--version" in s for s in kbuild._steps)


class TestKselftestSuiteResults:
    def test_names_identify_build_results(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        af_dir = tmp_path / "artifacts"
        (af_dir / "kselftest_targets.txt").write_text(
            "accel net/mptcp\n", encoding="utf-8"
        )
        (af_dir / "kselftest_metadata.json").write_text(
            json.dumps(
                {
                    "artifacts": {
                        "kselftest": [
                            "accel/test_accel",
                            "net/mptcp/mptcp_connect",
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

        assert kbuild._kselftest_suite_results("pass") == [
            ("build.kselftest.accel", "pass"),
            ("build.kselftest.net.mptcp", "pass"),
        ]


class FakeStorage:
    def __init__(self):
        self.single_uploads = []
        self.archive_uploads = []

    def upload_single(self, file_path, dest_path=""):
        self.single_uploads.append((file_path, dest_path))
        return f"https://storage.test/{dest_path}/{file_path[1]}"

    def upload_archive(
        self, archive_path, file_paths, dest_path="", archive_name=None
    ):
        self.archive_uploads.append(
            (archive_path, file_paths, dest_path, archive_name)
        )
        return {
            file_dst: f"https://storage.test/{dest_path}/{file_dst}"
            for _file_src, file_dst in file_paths
        }


class TestUploadArtifacts:
    def test_tuxmake_dtbs_use_archive_upload(self, tmp_path):
        kbuild = _kbuild(tmp_path, arch="arm64")
        af_dir = tmp_path / "artifacts"
        (af_dir / "dtbs" / "nested").mkdir(parents=True)
        (af_dir / "dtbs" / "board-a.dtb").write_bytes(b"dtb-a")
        (af_dir / "dtbs" / "nested" / "board-b.dtb").write_bytes(b"dtb-b")
        (af_dir / "dtbs.tar.xz").write_bytes(b"archive")

        storage = FakeStorage()
        kbuild._get_storage = lambda: storage
        kbuild._apijobname = "kbuild-clang-arm64"
        kbuild._node = {"id": "node123", "data": {}}
        kbuild._full_artifacts = {}

        node_af = kbuild.upload_artifacts()

        assert storage.single_uploads == []
        assert len(storage.archive_uploads) == 1
        archive_path, file_paths, dest_path, archive_name = (
            storage.archive_uploads[0]
        )
        assert archive_path == str(af_dir / "dtbs.tar.xz")
        assert dest_path == "kbuild-clang-arm64-node123"
        assert archive_name == "dtbs.tar.xz"
        assert sorted(file_dst for _file_src, file_dst in file_paths) == [
            "dtbs/board-a.dtb",
            "dtbs/nested/board-b.dtb",
        ]
        assert "dtbs/board-a.dtb" in kbuild._full_artifacts
        assert "dtbs/nested/board-b.dtb" in kbuild._full_artifacts
        assert node_af["dtbs/board-a_dtb"].endswith("dtbs/board-a.dtb")

    def test_make_dtbs_use_archive_upload(self, tmp_path):
        kbuild = _kbuild(tmp_path, arch="arm64")
        kbuild._backend = "make"
        kbuild._dtbs_check = False
        af_dir = tmp_path / "artifacts"
        (af_dir / "dtbs" / "nested").mkdir(parents=True)
        (af_dir / "dtbs" / "board-a.dtb").write_bytes(b"dtb-a")
        (af_dir / "dtbs" / "nested" / "board-b.dtb").write_bytes(b"dtb-b")
        (af_dir / "dtbs.tar.xz").write_bytes(b"archive")
        kbuild._artifacts = ["dtbs.tar.xz"]
        kbuild.verify_build()

        storage = FakeStorage()
        kbuild._get_storage = lambda: storage
        kbuild._apijobname = "kbuild-gcc-arm64"
        kbuild._node = {"id": "node123", "data": {}}
        kbuild._full_artifacts = {}

        node_af = kbuild.upload_artifacts()

        assert storage.single_uploads == []
        assert len(storage.archive_uploads) == 1
        archive_path, file_paths, _dest_path, archive_name = (
            storage.archive_uploads[0]
        )
        assert archive_path == str(af_dir / "dtbs.tar.xz")
        assert archive_name == "dtbs.tar.xz"
        assert sorted(file_dst for _file_src, file_dst in file_paths) == [
            "dtbs/board-a.dtb",
            "dtbs/nested/board-b.dtb",
        ]
        assert node_af["dtbs/board-a_dtb"].endswith("dtbs/board-a.dtb")


class TestPackageDtbs:
    def test_dtbs_are_packed_into_archive(self, tmp_path):
        kbuild = _kbuild(tmp_path, arch="arm64")
        kbuild._package_dtbs()
        steps = "\n".join(kbuild._steps)
        af_dir = kbuild._af_dir
        assert f"tar -C {af_dir} -cJf {af_dir}/dtbs.tar.xz dtbs" in steps
        # the archive is only built when at least one dtb was produced
        assert "-print -quit" in steps
        assert "dtbs.tar.xz" in kbuild._artifacts

    def test_archive_dropped_when_no_dtbs_built(self, tmp_path):
        kbuild = _kbuild(tmp_path, arch="arm64")
        kbuild._package_dtbs()
        kbuild.verify_build()
        assert "dtbs.tar.xz" not in kbuild._artifacts


class TestVerifyNetwork:
    def test_verify_network_success_immediate(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        mock_response = mock.Mock(status_code=200)
        with mock.patch("kernelci.kbuild.requests.get", return_value=mock_response) as mock_get:
            kbuild._verify_network(url="https://api.staging.kernelci.org", max_retries=3, retry_delay=0)
            mock_get.assert_called_once_with("https://api.staging.kernelci.org", timeout=10)

    def test_verify_network_retry_then_success(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        fail_response = mock.Mock(status_code=503)
        success_response = mock.Mock(status_code=200)
        with mock.patch("kernelci.kbuild.requests.get", side_effect=[fail_response, success_response]) as mock_get:
            with mock.patch("time.sleep"):
                kbuild._verify_network(url="https://api.kernelci.org", max_retries=3, retry_delay=0)
                assert mock_get.call_count == 2

    def test_verify_network_timeout_and_exhaustion(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        with mock.patch("kernelci.kbuild.requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
            with mock.patch("time.sleep"):
                with pytest.raises(RuntimeError) as exc_info:
                    kbuild._verify_network(url="https://custom.target.org", max_retries=2, retry_delay=0)
                assert "Network readiness check failed for https://custom.target.org" in str(exc_info.value)

    def test_verify_network_non_200_exhaustion(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        mock_response = mock.Mock(status_code=500)
        with mock.patch("kernelci.kbuild.requests.get", return_value=mock_response):
            with mock.patch("time.sleep"):
                with pytest.raises(RuntimeError) as exc_info:
                    kbuild._verify_network(max_retries=2, retry_delay=0)
                assert "https://api.kernelci.org" in str(exc_info.value)

