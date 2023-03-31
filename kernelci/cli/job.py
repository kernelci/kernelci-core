# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to generate and run KernelCI jobs"""

import kernelci.runtime
from .base import Args, Command, sub_main
from .base_api import APICommand


class cmd_init(APICommand):  # pylint: disable=invalid-name
    """Initialise job data before running it"""
    args = APICommand.args + [
        Args.api_token,
        {
            'name': 'job',
            'help': "Job name",
        },
    ]

    opt_args = APICommand.opt_args + [
        Args.indent, Args.id_only,
        {
            'name': '--input-node-id',
            'help': "ID of the input node",
        },
        {
            'name': '--input-node-json',
            'help': "Alternatively, path to the input node JSON file",
        },
    ]

    # This should in fact be using a generic method in the API class
    # pylint: disable=no-self-use
    def _create_node(self, api, input_node, job_config):
        job_node = {
            'parent': input_node['_id'],
            'name': job_config.name,
            'path': input_node['path'] + [job_config.name],
            'group': job_config.name,
            'artifacts': input_node['artifacts'],
            'revision': input_node['revision'],
        }
        return api.create_node(job_node)

    def _api_call(self, api, configs, args):
        if args.input_node_id:
            input_node = api.get_node(args.input_node_id)
        elif args.input_node_json:
            input_node = self._load_json(args.input_node_json)
        else:
            print("\
Invalid arguments.  Either --input-node-id or --input-node-json is required.")
            return False
        job_config = configs['jobs'][args.job]
        node = self._create_node(api, input_node, job_config)
        self._print_node(node, args.id_only, args.indent)
        return True


class cmd_generate(APICommand):  # pylint: disable=invalid-name
    """Generate a job definition file"""
    args = APICommand.args + [
        Args.runtime_config,
        {
            'name': '--platform',
            'help': "Name of the platform to run the job",
        },
    ]
    opt_args = APICommand.opt_args + [
        Args.storage_config,
        {
            'name': '--node-id',
            'help': "ID of the job's node",
        },
        {
            'name': '--node-json',
            'help': "Alternatively, path to the job's node JSON file",
        },
        {
            'name': '--output',
            'help': "Path of the directory where to generate the job data",
        },
    ]

    def _api_call(self, api, configs, args):
        if args.node_id:
            job_node = api.get_node(args.node_id)
        elif args.node_json:
            job_node = self._load_json(args.node_json)
        else:
            print("\
Invalid arguments.  Either --node-id or --node-json is required.")
            return False
        job_config = configs['jobs'][job_node['name']]
        platform_config = configs['device_types'][args.platform]
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(runtime_config)
        storage_config = (
            configs['storage_configs'][args.storage_config]
            if args.storage_config else None
        )
        params = runtime.get_params(
            job_node, job_config, platform_config, api.config, storage_config
        )
        job = runtime.generate(params, job_config)
        if args.output:
            output_file = runtime.save_file(job, args.output, params)
            print(f"Job saved in {output_file}")
        else:
            print(job)

        return True


class cmd_submit(Command):  # pylint: disable=invalid-name
    """Submit a job definition from a file"""
    args = Command.args + [
        Args.api_token, Args.runtime_config,
        {
            'name': 'job_path',
            'help': "Path of the job file to submit",
        },
    ]

    def __call__(self, configs, args):
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(runtime_config)
        job = runtime.submit(args.job_path)
        print(runtime.get_job_id(job))
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("job", globals(), args)
