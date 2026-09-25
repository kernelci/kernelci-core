# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tests for kernelci.kbuild build script generation and metadata"""

import json
import os
import subprocess
import sys
import types

import pytest

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
    kbuild._kconfig_adds = []
    kbuild._config_full = ""
    kbuild._backend = "tuxmake"
    kbuild._dtbs_check = True
    kbuild._kselftest = False
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


class TestFragments:
    @staticmethod
    def _fragments(tmp_path, fragments, fragment_configs):
        kbuild = _kbuild(tmp_path)
        kbuild._fragments = fragments
        kbuild._fragment_configs = fragment_configs
        kbuild._fragments_dir = os.path.join(kbuild._af_dir, "fragments")
        os.makedirs(kbuild._fragments_dir)
        return kbuild

    def test_make_target_is_not_written_to_a_fragment_file(self, tmp_path):
        kbuild = self._fragments(
            tmp_path,
            ["kselftest"],
            {"kselftest": {"configs": ["make:kselftest-merge"]}},
        )

        kconfig_adds = kbuild._parse_fragments()

        # kconfig would merge the directive as "unexpected data"
        assert kconfig_adds == ["make:kselftest-merge"]
        assert os.listdir(kbuild._fragments_dir) == []
        assert kbuild._artifacts == []
        assert kbuild._config_full == "+kselftest"

    def test_make_targets_are_split_from_config_symbols(self, tmp_path):
        kbuild = self._fragments(
            tmp_path,
            ["kselftest"],
            {
                "kselftest": {
                    "configs": [
                        "make:kselftest-merge",
                        "CONFIG_KUNIT=y",
                    ]
                }
            },
        )

        kconfig_adds = kbuild._parse_fragments()

        fragfile = os.path.join(kbuild._fragments_dir, "0.config")
        assert kconfig_adds == [fragfile, "make:kselftest-merge"]
        with open(fragfile) as f:
            assert f.read() == "CONFIG_KUNIT=y\n"

    def test_make_target_is_passed_to_tuxmake(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        kbuild._kconfig_adds = ["make:kselftest-merge"]

        parts = kbuild._tuxmake_base(kbuild._af_dir, "defconfig", [])

        assert "--kconfig-add=make:kselftest-merge" in parts

    def test_make_target_is_run_by_the_make_backend(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        kbuild._backend = "make"
        fragfile = os.path.join(kbuild._af_dir, "0.config")

        kbuild._merge_frags(["make:kselftest-merge", fragfile])

        steps = kbuild._steps
        merge = steps.index("make kselftest-merge")
        assert (
            steps.index(
                f"./scripts/kconfig/merge_config.sh -m .config {fragfile}"
            )
            > merge
        )
        # kselftest-merge needs a .config to merge into
        assert steps.index("make defconfig") < merge

    def test_tree_file_is_not_written_to_a_fragment_file(self, tmp_path):
        kbuild = self._fragments(
            tmp_path,
            ["kselftest-arm64"],
            {
                "kselftest-arm64": {
                    "configs": ["tree:tools/testing/selftests/arm64/config"]
                }
            },
        )

        kconfig_adds = kbuild._parse_fragments()

        assert kconfig_adds == ["tree:tools/testing/selftests/arm64/config"]
        assert os.listdir(kbuild._fragments_dir) == []
        assert kbuild._artifacts == []
        assert kbuild._config_full == "+kselftest-arm64"

    def test_tree_files_are_split_from_config_symbols(self, tmp_path):
        kbuild = self._fragments(
            tmp_path,
            ["kselftest-arm64"],
            {
                "kselftest-arm64": {
                    "configs": [
                        "tree:tools/testing/selftests/arm64/config",
                        "CONFIG_KUNIT=y",
                    ]
                }
            },
        )

        kconfig_adds = kbuild._parse_fragments()

        fragfile = os.path.join(kbuild._fragments_dir, "0.config")
        assert kconfig_adds == [
            fragfile,
            "tree:tools/testing/selftests/arm64/config",
        ]
        with open(fragfile) as f:
            assert f.read() == "CONFIG_KUNIT=y\n"

    @pytest.mark.parametrize(
        "path",
        [
            "../outside.config",
            "/etc/passwd",
            "tools/../../x",
            "",
            "tools/x; rm -rf /",
            "tools/$(id)",
            "tools/`id`",
            "tools/a b",
            "tools/x|y",
            ".",
            "tools/..",
        ],
    )
    def test_tree_file_outside_the_tree_is_refused(self, tmp_path, path):
        kbuild = self._fragments(
            tmp_path,
            ["bad"],
            {"bad": {"configs": [f"tree:{path}"]}},
        )
        failures = []
        kbuild.submit_failure = failures.append

        with pytest.raises(SystemExit):
            kbuild._parse_fragments()

        assert failures

    def test_tree_file_is_merged_by_the_make_backend(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        kbuild._backend = "make"

        kbuild._merge_frags(["tree:tools/testing/selftests/arm64/config"])

        steps = kbuild._steps
        merge = next(
            i
            for i, s in enumerate(steps)
            if "merge_config.sh -m .config tools/testing/selftests/arm64/config"
            in s
        )
        assert steps.index(f"cd {kbuild._srcdir}") < merge
        assert steps.index("make defconfig") < merge

    @pytest.mark.parametrize("present", [True, False])
    def test_make_backend_merges_a_tree_file_only_when_present(
        self, tmp_path, present
    ):
        kbuild = _kbuild(tmp_path)
        kbuild._backend = "make"
        kbuild._merge_frags(["tree:tools/testing/selftests/arm64/config"])
        merge = next(s for s in kbuild._steps if "merge_config.sh" in s)
        src = tmp_path / "linux"
        (src / "tools/testing/selftests/arm64").mkdir(parents=True)
        if present:
            (src / "tools/testing/selftests/arm64/config").write_text(
                "CONFIG_X=y\n"
            )
        merge_config = src / "scripts/kconfig/merge_config.sh"
        merge_config.parent.mkdir(parents=True)
        merge_config.write_text('#!/bin/sh\necho "$@" > merged\n')
        merge_config.chmod(0o755)
        script = tmp_path / "merge.sh"
        script.write_text(f"set -eE -o pipefail\ncd {src}\n{merge}\n")

        result = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True
        )

        assert result.returncode == 0
        merged = src / "merged"
        if present:
            assert merged.read_text().split() == [
                "-m",
                ".config",
                "tools/testing/selftests/arm64/config",
            ]
        else:
            assert not merged.exists()
            assert "not in this tree" in result.stdout

    def test_tree_file_is_passed_to_tuxmake_from_the_tree(self, tmp_path):
        kbuild = _kbuild(tmp_path)
        kbuild._kconfig_adds = ["tree:tools/testing/selftests/arm64/config"]

        parts = kbuild._tuxmake_base(kbuild._af_dir, "defconfig", [])

        path = os.path.join(
            kbuild._srcdir, "tools/testing/selftests/arm64/config"
        )
        assert not os.path.exists(path)
        added = [p for p in parts if path in p]
        assert len(added) == 1
        assert f"--kconfig-add={path}" in added[0]

    @pytest.mark.parametrize("present", [True, False])
    def test_tuxmake_adds_a_tree_file_only_when_present(
        self, tmp_path, present
    ):
        kbuild = _kbuild(tmp_path)
        kbuild._kconfig_adds = ["tree:tools/testing/selftests/arm64/config"]
        path = os.path.join(
            kbuild._srcdir, "tools/testing/selftests/arm64/config"
        )
        if present:
            os.makedirs(os.path.dirname(path))
            with open(path, "w") as f:
                f.write("CONFIG_X=y\n")
        parts = kbuild._tuxmake_base(kbuild._af_dir, "defconfig", [])
        added = next(p for p in parts if path in p)

        result = subprocess.run(
            [
                "bash",
                "-c",
                f"set -eE -o pipefail; set -- {added}; "
                'echo $#; for a; do echo "$a"; done',
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        expected = [f"--kconfig-add={path}"] if present else []
        assert result.stdout.splitlines() == [str(len(expected))] + expected


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


def _tuxmake_invocations(tmp_path, monkeypatch, kselftest, dtbs_check=False):
    monkeypatch.setitem(sys.modules, "tuxmake", None)
    kbuild = _kbuild(tmp_path)
    kbuild._dtbs_check = dtbs_check
    kbuild._kselftest = kselftest
    kbuild._extra_targets = []
    kbuild._fetch_firmware = lambda: None
    kbuild._build_with_tuxmake()
    return [s for s in kbuild._steps if s.startswith("tuxmake --runtime=null")]


class TestKselftestBuildDir:
    def test_kselftest_builds_in_kept_kernel_tree(self, tmp_path, monkeypatch):
        kernel, kselftest = _tuxmake_invocations(tmp_path, monkeypatch, True)
        build_dir = f"{tmp_path}/kernel_build"

        assert f"--build-dir={build_dir}" in kernel.split()
        assert f"--output-dir={tmp_path}/artifacts" in kernel.split()
        assert f"--build-dir={build_dir}" in kselftest.split()
        assert f"--output-dir={tmp_path}/kselftest_build" in kselftest.split()

    def test_no_kept_kernel_tree_without_kselftest(self, tmp_path, monkeypatch):
        (kernel,) = _tuxmake_invocations(tmp_path, monkeypatch, False)

        assert "--build-dir" not in kernel

    def test_no_kselftest_build_for_dtbs_check(self, tmp_path, monkeypatch):
        (kernel,) = _tuxmake_invocations(
            tmp_path, monkeypatch, False, dtbs_check=True
        )

        assert "--build-dir" not in kernel
        assert kernel.split()[-1] == "dtbs_check"


def _kbuild_from_params(monkeypatch, **params):
    monkeypatch.setenv("KCI_API_TOKEN", "test-token")
    params = {
        "arch": "arm64",
        "compiler": "gcc-14",
        "defconfig": "defconfig",
        "fragments": [],
        **params,
    }
    return KBuild(
        node={"artifacts": {"tarball": "https://storage.test/linux.tar.gz"}},
        jobname="kbuild-gcc-14-arm64",
        params=params,
        apiconfig="url: https://api.test\n",
    )


def _kbuild_from_json(tmp_path, monkeypatch, **params):
    kbuild = _kbuild_from_params(monkeypatch, **params)
    kbuild._storage_config = None
    kbuild._fragments_dir = None
    path = tmp_path / "kbuild.json"
    kbuild.serialize(str(path))
    return KBuild.from_json(str(path))


class TestKselftestFlag:
    def test_enabled_by_default(self, monkeypatch):
        assert _kbuild_from_params(monkeypatch)._kselftest is True

    def test_disabled_by_param(self, monkeypatch):
        kbuild = _kbuild_from_params(monkeypatch, kselftest="disable")
        assert kbuild._kselftest is False

    def test_disabled_for_dtbs_check(self, monkeypatch):
        kbuild = _kbuild_from_params(monkeypatch, dtbs_check=True)
        assert kbuild._kselftest is False

    def test_reload_keeps_enabled(self, tmp_path, monkeypatch):
        assert _kbuild_from_json(tmp_path, monkeypatch)._kselftest is True

    def test_reload_keeps_disabled_for_dtbs_check(self, tmp_path, monkeypatch):
        kbuild = _kbuild_from_json(tmp_path, monkeypatch, dtbs_check=True)
        assert kbuild._kselftest is False


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
