# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for kernelci.kbuild build script generation and metadata"""

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

    def test_probe_clang_fallback_without_tuxmake(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setitem(sys.modules, "tuxmake", None)
        kbuild = _kbuild(tmp_path, compiler="clang-21")
        kbuild._build_with_tuxmake()
        assert "clang --version || true" in kbuild._steps

    def test_no_probe_for_gcc_without_tuxmake(self, tmp_path, monkeypatch):
        monkeypatch.setitem(sys.modules, "tuxmake", None)
        kbuild = _kbuild(tmp_path, compiler="gcc-14")
        kbuild._build_with_tuxmake()
        assert not any("--version" in s for s in kbuild._steps)
