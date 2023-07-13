# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to generate and run KernelCI jobs"""

import kernelci.api.helper
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

    def _api_call(self, api, configs, args):
        if args.input_node_id:
            input_node = api.get_node(args.input_node_id)
        elif args.input_node_json:
            input_node = self._load_json(args.input_node_json)
        else:
            print("\
Invalid arguments.  Either --input-node-id or --input-node-json is required.")
            return False

        helper = kernelci.api.helper.APIHelper(api)
        job_config = configs['jobs'][args.job]
        job_node = helper.create_job_node(job_config, input_node)
        self._print_node(job_node, args.id_only, args.indent)
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
        Args.storage_config, Args.runtime_token,
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
        job = kernelci.runtime.Job(job_node, configs['jobs'][job_node['name']])
        job.platform_config = configs['device_types'][args.platform]
        job.storage_config = (
            configs['storage_configs'][args.storage_config]
            if args.storage_config else None
        )
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, token=args.runtime_token
        )
        params = runtime.get_params(job, api.config)
        job_data = runtime.generate(job, params)
        if args.output:
            output_file = runtime.save_file(job_data, args.output, params)
            print(f"Job saved in {output_file}")
        else:
            print(job_data)
        return True


class cmd_submit(Command):  # pylint: disable=invalid-name
    """Submit a job definition from a file"""
    args = Command.args + [
        Args.runtime_config,
        {
            'name': 'job_path',
            'help': "Path of the job file to submit",
        },
    ]
    opt_args = Command.opt_args + [
        Args.runtime_token,
        {
            'name': '--wait',
            'action': 'store_true',
            'help': "Wait for job to complete and get exit status code",
        },
    ]

    def __call__(self, configs, args):
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, token=args.runtime_token
        )
        job = runtime.submit(args.job_path)
        print(runtime.get_job_id(job))
        if args.wait:
            ret = runtime.wait(job)
            return ret == 0
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("job", globals(), args)
