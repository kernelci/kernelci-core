# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for kernelci.kbuild build script generation and metadata"""

import json
import os
import sys
import types

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
    kbuild._compiler_version = None
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


class TestPreserveTuxmakeMetadata:
    def test_preserves_tuxmake_metadata(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        af_dir = tmp_path / "artifacts"
        tux_meta = {
            "tuxmake": {"version": "1.40.0"},
            "compiler": {
                "name": "clang",
                "version": "21.1.8",
                "version_full": "Debian clang version 21.1.8",
            },
        }
        (af_dir / "metadata.json").write_text(json.dumps(tux_meta))
        kbuild._preserve_tuxmake_metadata()
        kbuild._write_metadata()
        preserved = json.loads((af_dir / "tuxmake_metadata.json").read_text())
        assert preserved == tux_meta
        own = json.loads((af_dir / "metadata.json").read_text())
        assert own["build"]["backend"] == "tuxmake"
        assert own["build"]["compiler_version"] == "Debian clang version 21.1.8"
        assert kbuild._compiler_version == "Debian clang version 21.1.8"

    def test_ignores_own_metadata(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        af_dir = tmp_path / "artifacts"
        own_meta = {"build": {"backend": "tuxmake"}}
        (af_dir / "metadata.json").write_text(json.dumps(own_meta))
        kbuild._preserve_tuxmake_metadata()
        kbuild._write_metadata()
        assert not (af_dir / "tuxmake_metadata.json").exists()
        own = json.loads((af_dir / "metadata.json").read_text())
        assert "compiler_version" not in own["build"]

    def test_handles_invalid_json(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        af_dir = tmp_path / "artifacts"
        (af_dir / "metadata.json").write_text("not json {")
        kbuild._preserve_tuxmake_metadata()
        kbuild._write_metadata()
        assert not (af_dir / "tuxmake_metadata.json").exists()
        own = json.loads((af_dir / "metadata.json").read_text())
        assert own["build"]["arch"] == "x86_64"

    def test_no_existing_metadata(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        af_dir = tmp_path / "artifacts"
        kbuild._preserve_tuxmake_metadata()
        kbuild._write_metadata()
        assert not (af_dir / "tuxmake_metadata.json").exists()
        own = json.loads((af_dir / "metadata.json").read_text())
        assert own["build"]["compiler"] == "clang-21"
        assert "compiler_version" not in own["build"]


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
