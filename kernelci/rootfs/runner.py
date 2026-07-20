# SPDX-License-Identifier: LGPL-2.1-or-later
"""Container execution primitives for rootfs builders."""

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


class ContainerError(RuntimeError):
    """Raised when the container engine or a container command fails."""


@dataclass(frozen=True)
class Mount:
    """A bind mount passed to the container engine."""

    source: Path
    target: str
    read_only: bool = False

    def as_argument(self) -> str:
        options = [
            "type=bind",
            f"source={self.source.resolve()}",
            f"target={self.target}",
        ]
        if self.read_only:
            options.append("readonly")
        return ",".join(options)


class ContainerRunner:
    """Run foreground, disposable containers through a Docker-style CLI."""

    VALID_PULL_POLICIES = ("always", "missing", "never")

    def __init__(
        self,
        engine: str = "docker",
        pull: str = "missing",
        verbose: bool = False,
    ):
        if not engine or any(char.isspace() for char in engine):
            raise ValueError("container engine must be one executable name")
        if pull not in self.VALID_PULL_POLICIES:
            raise ValueError(f"invalid image pull policy: {pull}")
        self.engine = engine
        self.pull = pull
        self.verbose = verbose

    def check_available(self) -> None:
        """Check that the selected engine and daemon are accessible."""
        self._execute([self.engine, "version"], capture=True)

    def build_command(
        self,
        image: str,
        command: Sequence[str],
        mounts: Sequence[Mount] = (),
        workdir: Optional[str] = None,
        user: Optional[str] = None,
        devices: Sequence[str] = (),
        environment: Optional[Dict[str, str]] = None,
        entrypoint: Optional[str] = None,
        pull: Optional[str] = None,
    ) -> List[str]:
        """Construct a container command without invoking a shell."""
        policy = pull or self.pull
        if policy not in self.VALID_PULL_POLICIES:
            raise ValueError(f"invalid image pull policy: {policy}")
        args = [self.engine, "run", "--rm", "--pull", policy]
        for mount in mounts:
            args.extend(("--mount", mount.as_argument()))
        for device in devices:
            args.extend(("--device", device))
        for key, value in sorted((environment or {}).items()):
            args.extend(("--env", f"{key}={value}"))
        if workdir:
            args.extend(("--workdir", workdir))
        if user:
            args.extend(("--user", user))
        if entrypoint:
            args.extend(("--entrypoint", entrypoint))
        args.append(image)
        args.extend(str(item) for item in command)
        return args

    def run(
        self,
        image: str,
        command: Sequence[str],
        **kwargs,
    ) -> None:
        """Run a container and stream its output to the caller's terminal."""
        args = self.build_command(image, command, **kwargs)
        self._execute(args)

    def normalize_ownership(self, image: str, path: Path) -> None:
        """Make a bind-mounted output tree owned by the invoking user."""
        self.run(
            image,
            ("-R", f"{os.getuid()}:{os.getgid()}", "/artifacts"),
            mounts=(Mount(path, "/artifacts"),),
            user="0:0",
            entrypoint="chown",
            pull="never",
        )

    def image_identity(self, image: str) -> Dict[str, object]:
        """Return the local image ID and immutable repository digests."""
        result = self._execute(
            [self.engine, "image", "inspect", image], capture=True
        )
        try:
            metadata = json.loads(result.stdout)[0]
        except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ContainerError(
                f"unable to parse image metadata for {image}"
            ) from exc
        return {
            "reference": image,
            "id": metadata.get("Id"),
            "repo_digests": metadata.get("RepoDigests") or [],
        }

    def _execute(
        self, args: Sequence[str], capture: bool = False
    ) -> subprocess.CompletedProcess:
        if self.verbose:
            print("+ " + shlex.join(args), flush=True)
        try:
            result = subprocess.run(
                list(args),
                check=False,
                text=True,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.PIPE if capture else None,
            )
        except FileNotFoundError as exc:
            raise ContainerError(
                f"container engine not found: {self.engine}"
            ) from exc
        if result.returncode:
            detail = (result.stderr or result.stdout or "").strip()
            suffix = f": {detail}" if detail else ""
            raise ContainerError(
                f"command failed with exit code {result.returncode}{suffix}"
            )
        return result
