# SPDX-License-Identifier: LGPL-2.1-or-later
"""Build and inspect KernelCI root filesystem images."""

import json
from pathlib import Path

import click
from pydantic import ValidationError

from kernelci.rootfs.builder import RootfsBuilder, RootfsBuildError
from kernelci.rootfs.config import (
    RootfsConfigError,
    find_rootfs_data_dir,
    load_rootfs_config,
    validate_debos_assets,
)
from kernelci.rootfs.runner import ContainerError, ContainerRunner

from . import kci


def config_options(func):
    """Add canonical configuration and data directory options."""
    func = click.option(
        "--data-dir",
        type=click.Path(file_okay=False, path_type=Path),
        help="Directory containing rootfs backend recipes and assets",
    )(func)
    return click.option(
        "--config",
        "config_path",
        type=click.Path(dir_okay=False, path_type=Path),
        help="Path to rootfs-configs.yaml",
    )(func)


def load_inputs(config_path, data_dir):
    """Load typed configuration and resolve its canonical data directory."""
    try:
        configs = load_rootfs_config(config_path)
        rootfs_data = find_rootfs_data_dir(data_dir)
        validate_debos_assets(configs, rootfs_data)
    except (OSError, RootfsConfigError, ValidationError) as exc:
        raise click.ClickException(str(exc)) from exc
    return configs, rootfs_data


@kci.group(name="rootfs")
def kci_rootfs():
    """Build and inspect root filesystem images."""


@kci_rootfs.command(name="list")
@config_options
@click.option(
    "--type",
    "rootfs_type",
    type=click.Choice(("debos", "buildroot")),
    help="Only show configurations using this backend",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json")),
    default="text",
    show_default=True,
)
def list_configs(config_path, data_dir, rootfs_type, output_format):
    """List available rootfs configurations."""
    configs, _ = load_inputs(config_path, data_dir)
    entries = [
        {
            "name": name,
            "type": config.rootfs_type,
            "architectures": config.arch_list,
        }
        for name, config in configs.rootfs_configs.items()
        if rootfs_type is None or config.rootfs_type == rootfs_type
    ]
    if output_format == "json":
        click.echo(json.dumps(entries, separators=(",", ":")))
    else:
        for entry in entries:
            click.echo(entry["name"])


@kci_rootfs.command
@click.argument("name")
@config_options
@click.option("--arch", help="Only show this architecture")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json")),
    default="text",
    show_default=True,
)
def variants(name, config_path, data_dir, arch, output_format):
    """List build variants for one rootfs configuration."""
    configs, _ = load_inputs(config_path, data_dir)
    config = configs.rootfs_configs.get(name)
    if config is None:
        raise click.ClickException(f"unknown rootfs configuration: {name}")
    if arch and arch not in config.arch_list:
        raise click.ClickException(
            f"architecture '{arch}' is not supported by {name}"
        )
    arches = [arch] if arch else config.arch_list
    entries = [
        {"name": name, "arch": item, "type": config.rootfs_type}
        for item in arches
    ]
    if output_format == "json":
        click.echo(json.dumps(entries, separators=(",", ":")))
    else:
        for entry in entries:
            click.echo(f"{entry['name']} {entry['arch']} {entry['type']}")


@kci_rootfs.command
@config_options
def validate(config_path, data_dir):
    """Validate rootfs configuration, recipes, scripts, and overlays."""
    configs, _ = load_inputs(config_path, data_dir)
    click.echo(
        f"Validated {len(configs.rootfs_configs)} rootfs configurations."
    )


@kci_rootfs.command
@click.argument("name")
@config_options
@click.option("--arch", multiple=True, help="Architecture to build; repeatable")
@click.option(
    "--all-arches", is_flag=True, help="Build every configured architecture"
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("output"),
    show_default=True,
)
@click.option(
    "--cache-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path(".cache/kernelci/rootfs"),
    show_default=True,
)
@click.option(
    "--debos-image",
    default="ghcr.io/kernelci/debos:kernelci",
    show_default=True,
)
@click.option(
    "--buildroot-image",
    default="ghcr.io/kernelci/buildroot:kernelci",
    show_default=True,
)
@click.option(
    "--pull",
    type=click.Choice(ContainerRunner.VALID_PULL_POLICIES),
    default="missing",
    show_default=True,
)
@click.option("--container-engine", default="docker", show_default=True)
@click.option("--keep-failed", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
def build(
    name,
    config_path,
    data_dir,
    arch,
    all_arches,
    output_dir,
    cache_dir,
    debos_image,
    buildroot_image,
    pull,
    container_engine,
    keep_failed,
    verbose,
):
    """Build one rootfs configuration for selected architectures."""
    requested_arches = list(arch or [])
    if bool(requested_arches) == bool(all_arches):
        raise click.UsageError("use either --arch (repeatable) or --all-arches")
    configs, rootfs_data = load_inputs(config_path, data_dir)
    config = configs.rootfs_configs.get(name)
    if config is None:
        raise click.ClickException(f"unknown rootfs configuration: {name}")
    arches = config.arch_list if all_arches else requested_arches
    unsupported = [item for item in arches if item not in config.arch_list]
    if unsupported:
        raise click.ClickException(
            f"unsupported architecture for {name}: {', '.join(unsupported)}"
        )
    if len(arches) != len(set(arches)):
        raise click.ClickException("duplicate --arch values are not allowed")

    runner = ContainerRunner(container_engine, pull=pull, verbose=verbose)
    try:
        runner.check_available()
        builder = RootfsBuilder(
            configs,
            rootfs_data,
            output_dir,
            cache_dir,
            runner,
            images={
                "debos": debos_image,
                "buildroot": buildroot_image,
            },
            keep_failed=keep_failed,
        )
    except (OSError, RootfsConfigError, ContainerError) as exc:
        raise click.ClickException(str(exc)) from exc

    failures = []
    for item in arches:
        click.echo(f"Building {name}/{item} ({config.rootfs_type})")
        try:
            artifact_dir = builder.build(name, item)
            click.echo(f"Artifacts: {artifact_dir}")
        except (OSError, RootfsBuildError, ContainerError) as exc:
            failures.append(f"{item}: {exc}")
            click.echo(f"Build failed for {name}/{item}: {exc}", err=True)
    if failures:
        raise click.ClickException("; ".join(failures))
