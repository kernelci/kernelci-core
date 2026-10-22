# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exercise CA trust validation against real certificates and cleanup."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

from kernelci.rootfs.backends.buildroot import BUILD_SCRIPT

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "config/rootfs/debos/scripts/verify-ca-certificates.py"
spec = importlib.util.spec_from_file_location("verify_rootfs_ca", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


@pytest.fixture
def store(tmp_path):
    directory = tmp_path / "etc/ssl/certs"
    directory.mkdir(parents=True)
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "ec",
            "-pkeyopt",
            "ec_paramgen_curve:P-256",
            "-nodes",
            "-subj",
            "/CN=KernelCI rootfs test CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-keyout",
            str(tmp_path / "test.key"),
            "-out",
            str(directory / "ca-certificates.crt"),
        ],
        check=True,
        capture_output=True,
    )
    return directory


def test_accepts_normal_ca_bundle(store):
    verifier.verify(store)


@pytest.mark.parametrize(
    "location",
    ["ca-certificates.crt", "emsign.pem", "emsign.crt", "12345678.0"],
)
def test_rejects_compromised_trust_in_bundle_or_capath(store, location):
    certificate = ROOT / "tests/data/emsign-ecc-root-ca-g3.pem"
    (store / location).write_bytes(certificate.read_bytes())
    with pytest.raises(ValueError, match="Distrusted eMudhra"):
        verifier.verify(store)


def test_rejects_missing_bundle(store):
    (store / "ca-certificates.crt").unlink()
    with pytest.raises(FileNotFoundError):
        verifier.verify(store)


def test_rejects_trusted_pem_anchor_mixed_with_normal_ca(store):
    trusted = subprocess.run(
        [
            "openssl",
            "x509",
            "-trustout",
            "-in",
            str(ROOT / "tests/data/emsign-ecc-root-ca-g3.pem"),
        ],
        check=True,
        capture_output=True,
    ).stdout
    with (store / "ca-certificates.crt").open("ab") as bundle:
        bundle.write(trusted)
    with pytest.raises(ValueError, match="Distrusted eMudhra"):
        verifier.verify(store)


def test_accepts_legitimate_trusted_pem_encoding(store):
    bundle = store / "ca-certificates.crt"
    trusted = subprocess.run(
        ["openssl", "x509", "-trustout", "-in", str(bundle)],
        check=True,
        capture_output=True,
    ).stdout
    bundle.write_bytes(trusted)
    verifier.verify(store)


@pytest.mark.parametrize(
    "contents", [b"", b"-----BEGIN CERTIFICATE-----\ntruncated"]
)
def test_rejects_empty_or_malformed_bundle(store, contents):
    (store / "ca-certificates.crt").write_bytes(contents)
    with pytest.raises(ValueError, match="Invalid CA"):
        verifier.verify(store)


def test_rejects_dangling_ca_symlink(store):
    (store / "test.pem").symlink_to("/missing/rootfs-test-ca.crt")
    with pytest.raises(FileNotFoundError):
        verifier.verify(store)


def test_absolute_ca_symlink_uses_rootfs_source(store, tmp_path):
    source = tmp_path / "usr/share/ca-certificates/test.crt"
    source.parent.mkdir(parents=True)
    source.write_bytes((store / "ca-certificates.crt").read_bytes())
    (store / "test.pem").symlink_to("/usr/share/ca-certificates/test.crt")
    verifier.verify(store)
    source.write_bytes(
        (ROOT / "tests/data/emsign-ecc-root-ca-g3.pem").read_bytes()
    )
    with pytest.raises(ValueError, match="Distrusted eMudhra"):
        verifier.verify(store)


def test_resolves_absolute_store_directory_symlink(store, tmp_path):
    relocated = tmp_path / "usr/lib/ssl/certs"
    relocated.parent.mkdir(parents=True)
    store.rename(relocated)
    store.symlink_to("/usr/lib/ssl/certs")
    verifier.verify(store)


def test_crush_preserves_individual_ca_sources(store, tmp_path):
    source = tmp_path / "usr/share/ca-certificates/mozilla/test.crt"
    source.parent.mkdir(parents=True)
    source.write_bytes((store / "ca-certificates.crt").read_bytes())
    (store / "test.pem").symlink_to(
        "../../../usr/share/ca-certificates/mozilla/test.crt"
    )
    subprocess.run(
        [
            "sh",
            str(ROOT / "config/rootfs/debos/scripts/crush.sh"),
            "misc_directories",
        ],
        cwd=tmp_path,
        check=True,
    )
    verifier.verify(store)
    assert (store / "test.pem").read_bytes() == source.read_bytes()


@pytest.mark.parametrize("poisoned", [False, True])
def test_buildroot_drops_stale_images_and_gates_publication(
    store, tmp_path, poisoned
):
    repo = tmp_path / "repo"
    for directory in ("target", "host"):
        certificates = repo / "output" / directory / "etc/ssl/certs"
        certificates.mkdir(parents=True)
        (certificates / "ca-certificates.crt").write_bytes(
            (store / "ca-certificates.crt").read_bytes()
        )
    if poisoned:
        (repo / "output/target/etc/ssl/certs/ca-certificates.crt").write_bytes(
            (ROOT / "tests/data/emsign-ecc-root-ca-g3.pem").read_bytes()
        )
    images = repo / "output/images"
    images.mkdir()
    (images / "old-format.rootfs.tar.xz").write_bytes(b"stale image")
    fragments = repo / "configs/frags"
    fragments.mkdir(parents=True)
    build = fragments / "build"
    build.write_text(
        "#!/bin/sh\nset -eu\nmkdir -p output/images\n"
        "printf new > output/images/rootfs.cpio.gz\n"
    )
    build.chmod(0o755)
    artifacts = tmp_path / "published"
    artifacts.mkdir()
    (artifacts / "previous").write_bytes(b"last successful output")
    # Exercise the real build/validation/publication commands without Git or
    # toolchain downloads. Only sandbox mount paths are substituted.
    script = "arch=x86\n" + BUILD_SCRIPT.split("git clean -fd\n", 1)[1]
    script = script.replace(
        "=/configs/", "=" + str(ROOT / "config/rootfs") + "/"
    )
    script = script.replace("/artifacts", str(artifacts))
    result = subprocess.run(
        ["bash", "-euc", script, "rootfs-test", "baseline"],
        cwd=repo,
        capture_output=True,
    )
    if poisoned:
        assert result.returncode != 0
        assert b"Distrusted eMudhra" in result.stderr
        assert (
            artifacts / "previous"
        ).read_bytes() == b"last successful output"
    else:
        assert result.returncode == 0, result.stderr.decode()
        names = sorted(p.name for p in artifacts.iterdir())
        assert names == ["rootfs.cpio.gz"]
        assert (artifacts / "rootfs.cpio.gz").read_bytes() == b"new"
