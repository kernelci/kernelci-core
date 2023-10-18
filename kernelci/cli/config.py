# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage the KernelCI YAML pipeline configuration"""

import os

import click
import yaml

import kernelci.config
from . import Args, kci


@kci.group(name='config')
def kci_config():
    """Manage the KernelCI YAML pipeline configuration"""


@kci_config.command
@Args.config
def list_files(config):
    """List the YAML configuration files to be loaded"""
    paths = kernelci.config.get_config_paths(config)
    for path in paths:
        for yaml_file, _ in kernelci.config.iterate_yaml_files(path):
            click.echo(yaml_file)


@kci_config.command
@Args.config
@Args.verbose
def validate(config, verbose):
    """Validate the YAML pipeline configuration"""
    sections = [
        'jobs',
        'runtimes',
        'scheduler',
    ]
    err = kernelci.config.validate_yaml(config, sections)
    if err:
        raise click.ClickException(err)
    if verbose:
        click.echo("YAML configuration validation succeeded.")


@kci_config.command
@click.argument('section', required=False)
@Args.config
@Args.indent
@click.option(
    '-r', '--recursive', is_flag=True,
    help="Dump recursively the contents of each entry"
)
def dump(section, config, indent, recursive):
    """Dump entries from the SECTION of the pipeline YAML configuration"""
    data = kernelci.config.load(config)
    if section:
        for step in section.split('.'):
            data = (
                data.get(step, {}) if isinstance(data, dict)
                else getattr(data, step)
            )
    if not data:
        raise click.ClickException(f"Section not found: {section}")
    if isinstance(data, dict) and not recursive:
        keys = list(sorted(data.keys()))
        _, lines = os.get_terminal_size()
        echo = click.echo_via_pager if len(keys) >= lines else click.echo
        echo('\n'.join(keys))
    elif isinstance(data, (str, int, float)):
        click.echo(data)
    else:
        echo = click.echo_via_pager if recursive else click.echo
        echo(yaml.dump(data, indent=indent))
