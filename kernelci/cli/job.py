# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to generate and run KernelCI jobs"""

import click

import kernelci.config
import kernelci.runtime
from . import (
    Args,
    catch_error,
    echo_json,
    get_api,
    get_api_helper,
    kci,
)


@kci.group(name='job')
def kci_job():
    """Manage KernelCI jobs"""


@kci_job.command(secrets=True)
@click.argument('name')
@click.argument('input_node_id')
@Args.config
@Args.api
@Args.indent
@catch_error
def new(name, input_node_id, config,  # pylint: disable=too-many-arguments
        api, indent, secrets):
    """Create a new job node"""
    configs = kernelci.config.load(config)
    helper = get_api_helper(configs, api, secrets)
    input_node = helper.api.node.get(input_node_id)
    job_config = configs['jobs'][name]
    job_node = helper.create_job_node(job_config, input_node)
    echo_json(job_node, indent)


@kci_job.command(secrets=True)
@click.argument('node-id')
@click.option(
    '--platform', required=True,
    help="Name of the platform to run the job"
)
@click.option(
    '--output',
    help="Path of the directory where to generate the job data"
)
@Args.runtime
@Args.storage
@Args.config
@Args.api
@catch_error
def generate(node_id,  # pylint: disable=too-many-arguments, too-many-locals
             runtime, storage, platform, output, config, api, secrets):
    """Generate a job definition in a file"""
    configs = kernelci.config.load(config)
    api = get_api(configs, api, secrets)
    job_node = api.node.get(node_id)
    job = kernelci.runtime.Job(job_node, configs['jobs'][job_node['name']])
    job.platform_config = configs['platforms'][platform]
    job.storage_config = (
        configs['storage'][storage]
        if storage else None
    )
    runtime_config = configs['runtimes'][runtime]
    runtime = kernelci.runtime.get_runtime(
        runtime_config, token=secrets.api.runtime_token)
    params = runtime.get_params(job, api.config)
    if not params:
        raise click.ClickException("Invalid job parameters, aborting...")
    job_data = runtime.generate(job, params)
    if output:
        output_file = runtime.save_file(job_data, output, params)
        click.echo(f"Job saved in {output_file}")
    else:
        click.echo(job_data)


@kci_job.command(secrets=True)
@click.argument('job-path')
@click.option('--wait', is_flag=True)
@Args.runtime
@Args.config
@catch_error
def submit(runtime, job_path, wait, config, secrets):
    """Submit a job definition to its designated runtime"""
    configs = kernelci.config.load(config)
    runtime_config = configs['runtimes'][runtime]
    runtime = kernelci.runtime.get_runtime(
        runtime_config, token=secrets.api.runtime_token
    )
    job = runtime.submit(job_path)
    click.echo(runtime.get_job_id(job))
    if wait:
        ret = runtime.wait(job)
        click.echo(f"Job completed with status: {ret}")
