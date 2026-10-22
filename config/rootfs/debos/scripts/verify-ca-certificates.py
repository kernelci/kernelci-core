#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Reject broken or compromised rootfs CA stores before publication."""

import argparse
import base64
import hashlib
import os
import re
import subprocess
from collections import deque
from pathlib import Path

# Compromised intermediates and their signing roots, including cross-signs.
# https://seclists.org/oss-sec/2026/q4/233
# https://emudhra.we-have-a-problem.com/impacted-intermediates.json
BLOCKED_SPKI_SHA256 = {
    "bd153ed7b0434f6886b17bce8bbe84ed340c7132d702a8f4fa318f756ecbd6f3",
    "c619e4780ed8e0abeda24ad732567de4383a7ea941338f6d1a7d1b49ac792fe9",
    "8d417db2dd8bf5e3084d1e3f196d583849d81bdd4c00c70b9d39369e96b8c782",
    "e0254c7fcdc265e2f0f8a428dabb75ab4ae039b4872d62f5ee57f0877d5a8a41",
    "43bffa19d6ef651451f6841e019931e96f6f2eaeff28ab4b6f1ce4576de2717b",
    "ebed6475c2c2d80fcb199f3fe8dd6e6b3ce60b77eb15d4e42c3dec0c6f5b5105",
    "5c0660a2b164910d8ff589c18e14552e9e0ec237dcefe2cb736d41a4811f81a0",
    "63ecefee431d49523bc1136c4e72d0206a477086caf606cd5cf025686c109cf8",
    "49dd353dc2b919a3770645117d0e60c16115e7d1bc259eefe734b00ea434fe5f",
    "ec4ffa1ad0ac88081314b7aaffef6a91f97cd57291bb5ba686c5415f5eb4f6b6",
    "92c063d67e8f14db71d288e11266ffdaf69cbf115f7bab14f3bc2f68d25e0e30",
}
CERTIFICATE = re.compile(
    rb"-----BEGIN (CERTIFICATE|TRUSTED CERTIFICATE)-----\s*"
    rb"(.*?)\s*-----END \1-----",
    re.DOTALL,
)


def in_root(path: Path, root: Path) -> Path:
    """Resolve absolute rootfs links inside the image, never on the builder."""
    remaining = deque(path.relative_to(root).parts)
    current = root
    links = 0
    while remaining:
        part = remaining.popleft()
        if part == "..":
            if current == root:
                raise ValueError(f"CA path escapes rootfs: {path}")
            current = current.parent
            continue
        current /= part
        if current.is_symlink():
            links += 1
            if links > 40:
                raise ValueError(f"CA symlink loop: {path}")
            target = Path(os.readlink(current))
            current = root if target.is_absolute() else current.parent
            parts = target.parts[1:] if target.is_absolute() else target.parts
            remaining.extendleft(reversed(parts))
    return current


def verify(store: Path) -> None:
    """Check the bundle and individual anchors used by CApath clients."""
    store = store.absolute()
    # Shared <rootfs>/etc/ssl/certs layout, including the host SDK.
    root = store.parents[2]
    store = in_root(store, root)
    anchors = {store / "ca-certificates.crt"}
    anchors.update(store.glob("*.crt"))
    anchors.update(store.glob("*.pem"))
    anchors.update(store.glob("????????.[0-9]*"))
    seen = set()
    for anchor in sorted(anchors):
        data = in_root(anchor, root).read_bytes()
        certificates = CERTIFICATE.findall(data)
        if not certificates or len(certificates) != data.count(b"-----BEGIN "):
            raise ValueError(f"Invalid CA certificate file: {anchor}")
        for _label, certificate in certificates:
            encoded = b"".join(certificate.split())
            der = base64.b64decode(encoded, validate=True)
            if der in seen:
                continue
            public_key = subprocess.run(
                ["openssl", "x509", "-inform", "DER", "-noout", "-pubkey"],
                input=der,
                check=True,
                capture_output=True,
            ).stdout
            spki = base64.b64decode(b"".join(public_key.splitlines()[1:-1]))
            if hashlib.sha256(spki).hexdigest() in BLOCKED_SPKI_SHA256:
                raise ValueError(f"Distrusted eMudhra chain anchor: {anchor}")
            seen.add(der)
    print(f"Verified {len(seen)} CA certificates in {store}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", type=Path)
    arguments = parser.parse_args()
    try:
        verify(arguments.store)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"CA trust verification failed: {error}\n")
