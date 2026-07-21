#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Deprecated compatibility wrapper for :command:`kci rootfs`."""

import argparse
import sys
from pathlib import Path

from kernelci.cli import kci
from kernelci.cli import rootfs as rootfs_cli  # noqa: F401
from kernelci.rootfs.config import load_rootfs_config

DEPRECATION = (
    "kci_rootfs is deprecated and will be removed in the next minor release; "
    "use 'kci rootfs' instead."
)


def _config_file(path):
    if not path:
        return None
    candidate = Path(path)
    return (
        candidate / "rootfs-configs.yaml" if candidate.is_dir() else candidate
    )


def _data_dir(path):
    if not path:
        return None
    candidate = Path(path)
    if candidate.name in ("debos", "buildroot"):
        return candidate.parent
    return candidate


def make_parser():
    parser = argparse.ArgumentParser(prog="kci_rootfs")
    parser.add_argument("--yaml-config")
    parser.add_argument("--extra-config", action="append", default=[])
    parser.add_argument("--settings")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("--verbose", action="store_true")

    list_configs = commands.add_parser("list_configs")
    list_configs.add_argument("--rootfs-type", choices=("debos", "buildroot"))

    list_variants = commands.add_parser("list_variants")
    list_variants.add_argument("--rootfs-config")
    list_variants.add_argument("--rootfs-type", action="append")
    list_variants.add_argument("--arch", action="append")

    build = commands.add_parser("build")
    build.add_argument("--rootfs-config", required=True)
    build.add_argument("--arch", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--data-path")

    upload = commands.add_parser("upload")
    upload.add_argument("--rootfs-dir")
    upload.add_argument("--upload-path")
    upload.add_argument("--storage-config")
    upload.add_argument("--storage-cred")
    return parser


def _common_args(args):
    translated = []
    config_file = _config_file(args.yaml_config)
    if config_file:
        translated.extend(("--config", str(config_file)))
    return translated


def _list_legacy_variants(args):
    config_file = _config_file(args.yaml_config)
    configs = load_rootfs_config(config_file)
    names = (
        [args.rootfs_config]
        if args.rootfs_config
        else list(configs.rootfs_configs)
    )
    requested_arches = set(args.arch or [])
    requested_types = set(args.rootfs_type or [])
    for name in names:
        config = configs.rootfs_configs.get(name)
        if config is None:
            raise SystemExit(f"unknown rootfs configuration: {name}")
        if requested_types and config.rootfs_type not in requested_types:
            continue
        for arch in config.arch_list:
            if not requested_arches or arch in requested_arches:
                print(f"{name} {arch} {config.rootfs_type}")


def main(argv=None):
    print(f"Warning: {DEPRECATION}", file=sys.stderr)
    args = make_parser().parse_args(argv)
    common = _common_args(args)

    if args.command == "validate":
        command = ["rootfs", "validate", *common]
    elif args.command == "list_configs":
        command = ["rootfs", "list", *common]
        if args.rootfs_type:
            command.extend(("--type", args.rootfs_type))
    elif args.command == "list_variants":
        _list_legacy_variants(args)
        return
    elif args.command == "build":
        data_dir = _data_dir(args.data_path)
        command = [
            "rootfs",
            "build",
            args.rootfs_config,
            "--arch",
            args.arch,
            "--output-dir",
            str(Path(args.output) / "_install_"),
            *common,
        ]
        if data_dir:
            command.extend(("--data-dir", str(data_dir)))
    else:
        raise SystemExit(
            "kci_rootfs upload has been removed; publication belongs to the "
            "deployment workflow"
        )

    kci.main(args=command, prog_name="kci", standalone_mode=True)


if __name__ == "__main__":
    main()
