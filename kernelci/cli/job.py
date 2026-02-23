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
@click.option(
    '--platform',
    help="Name of the platform to create the node for"
)
@Args.runtime
@Args.config
@Args.api
@Args.indent
@catch_error
def new(name, input_node_id, *, platform,  # pylint: disable=too-many-arguments
        runtime, config, api, indent, secrets):
    """Create a new job node"""
    configs = kernelci.config.load(config)
    helper = get_api_helper(configs, api, secrets)
    input_node = helper.api.node.get(input_node_id)
    if not input_node:
        raise click.ClickException("Node not found with the provided ID")
    job_config = configs['jobs'][name]
    platform_config = None
    if platform:
        if platform not in configs['platforms']:
            raise click.ClickException(f"Invalid platform {platform}")
        platform_config = configs['platforms'][platform]
    if runtime:
        if runtime not in configs['runtimes']:
            raise click.ClickException(f"Invalid runtime {runtime}")
        runtime = kernelci.runtime.get_runtime(
            configs['runtimes'][runtime], token=secrets.api.runtime_token,
            custom_template_dir=config[0] if config else None)
    job_node = helper.create_job_node(job_config, input_node,
                                      platform=platform_config, runtime=runtime)
    if job_node:
        echo_json(job_node, indent)


@kci_job.command(secrets=True)
@click.argument('node-id')
@click.option(
    '--platform',
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
def generate(node_id, *,  # pylint: disable=too-many-arguments, too-many-locals
             runtime, storage, platform, output, config, api, secrets):
    """Generate a job definition in a file"""
    configs = kernelci.config.load(config)
    api = get_api(configs, api, secrets)
    job_node = api.node.get(node_id)
    if job_node.get('parent'):
        parent_node = api.node.get(job_node['parent'])
        if job_node.get('artifacts'):
            job_node['artifacts'].update(parent_node['artifacts'])
        else:
            job_node['artifacts'] = parent_node['artifacts']
    jobs_section = configs.get('jobs', None)
    if jobs_section is None:
        raise click.ClickException("No jobs section found in the config")
    job_config = jobs_section.get(job_node['name'], None)
    if job_config is None:
        raise click.ClickException(f"Job {job_node['name']} not found in the config")
    job = kernelci.runtime.Job(job_node, job_config)
    if platform is None:
        if 'platform' not in job_node['data']:
            raise click.ClickException(
                "Platform absent from input node data, please provide --platform argument"
            )
        platform = job_node['data']['platform']
    job.platform_config = configs['platforms'][platform]
    job.storage_config = (
        configs['storage'][storage]
        if storage else None
    )
    runtime = _get_runtime(runtime, config, secrets)
    try:
        params = runtime.get_params(job, api.config)
    except ValueError as exc:
        raise click.ClickException(
            f"Invalid job parameters: {exc}"
        ) from exc
    # Process potential f-strings in `params` with configured job params
    # and platform attributes
    kernel_revision = job_node['data']['kernel_revision']['version']
    extra_args = {
        'krev': f"{kernel_revision['version']}.{kernel_revision['patchlevel']}"
    }
    extra_args.update(job.config.params)
    params = job.platform_config.format_params(params, extra_args)
    job_data = runtime.generate(job, params)
    if output:
        output_file = runtime.save_file(job_data, output, params)
        click.echo(f"Job saved in {output_file}")
    else:
        click.echo(job_data)


def _get_runtime(runtime, config, secrets):
    if not runtime:
        raise click.ClickException("Runtime not specified, please provide --runtime argument")
    configs = kernelci.config.load(config)
    runtime_section = configs.get('runtimes', None)
    if runtime_section is None:
        raise click.ClickException("No runtime section found in the config")
    runtime_config = runtime_section.get(runtime, None)
    if runtime_config is None:
        raise click.ClickException(f"Runtime {runtime} not found in the config")
    runtime = kernelci.runtime.get_runtime(
        runtime_config, token=secrets.api.runtime_token,
        custom_template_dir=config[0] if config else None
    )
    return runtime


@kci_job.command(secrets=True)
@click.argument('job-path')
@click.option('--wait', is_flag=True)
@Args.api
@Args.runtime
@Args.config
@catch_error
def submit(job_path, *, runtime, wait,  # pylint: disable=too-many-arguments
           config, secrets, api):  # pylint: disable=unused-argument
    """Submit a job definition to its designated runtime"""
    configs = kernelci.config.load(config)
    runtime_config = configs['runtimes'][runtime]
    runtime = kernelci.runtime.get_runtime(
        runtime_config, token=secrets.api.runtime_token,
        custom_template_dir=config[0] if config else None
    )
    job = runtime.submit(job_path)
    click.echo(runtime.get_job_id(job))
    if wait:
        ret = runtime.wait(job)
        click.echo(f"Job completed with status: {ret}")
