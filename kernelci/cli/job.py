# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to generate and run KernelCI jobs"""

import json

import click

import kernelci.api
import kernelci.config
import kernelci.api.helper
import kernelci.runtime
from . import Args, kci, catch_http_error


@kci.group(name='job')
def kci_job():
    """Manage KernelCI jobs"""


@kci_job.command(secrets=True)
@click.argument('name')
@click.option('--node-id')
@click.option('--node-json')
@Args.config
@Args.api
@Args.indent
@catch_http_error
def new(name, node_id, node_json, config,  # pylint: disable=too-many-arguments
        api, indent, secrets):
    """Create a new job node"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    helper = kernelci.api.helper.APIHelper(api)
    if node_id:
        input_node = api.get_node(node_id)
    elif node_json:
        input_node = helper.load_json(node_json)
    else:
        raise click.ClickException("Either --node-id or --node-json \
is required.")
    job_config = configs['jobs'][name]
    job_node = helper.create_job_node(job_config, input_node)
    click.echo(json.dumps(job_node, indent=indent))


@kci_job.command(secrets=True)
@click.argument('node-id')
@click.option('--platform', help="Name of the platform to run the job",
              required=True)
@click.option('--output', help="Path of the directory where to generate \
              the job data")
@Args.runtime
@Args.storage
@Args.config
@Args.api
@catch_http_error
def generate(node_id,  # pylint: disable=too-many-arguments, too-many-locals
             runtime, storage, platform, output, config, api, secrets):
    """Generate a job definition in a file"""
    configs = kernelci.config.load(config)
    api_config = configs['api'][api]
    api = kernelci.api.get_api(api_config, secrets.api.token)
    job_node = api.get_node(node_id)
    job = kernelci.runtime.Job(job_node, configs['jobs'][job_node['name']])
    job.platform_config = configs['device_types'][platform]
    job.storage_config = (
        configs['storage'][storage]
        if storage else None
    )
    runtime_config = configs['runtimes'][runtime]
    runtime = kernelci.runtime.get_runtime(
        runtime_config, token=secrets.api.runtime_token)
    params = runtime.get_params(job, api.config)
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
@catch_http_error
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
