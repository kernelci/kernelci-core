# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to generate and run KernelCI jobs"""

import yaml

import kernelci.runtime
from .base import APICommand, Args, sub_main


class cmd_register(APICommand):  # pylint: disable=invalid-name
    """Create a new node before running a job"""
    args = APICommand.args + [Args.plan]

    opt_args = APICommand.opt_args + [
        Args.indent,
        {
            'name': '--input-node-id',
            'help': "ID of the input node",
        },
        {
            'name': '--input-node-json',
            'help': "Alternatively, path to the input node JSON file",
        },
        {
            'name': '--id-only',
            'action': 'store_true',
            'help': "Only print the node ID rather than the full node data",
        },
    ]

    # This should in fact be using a generic method in the API class
    # pylint: disable=no-self-use
    def _create_node(self, api, input_node, plan_config):
        job_node = {
            'parent': input_node['_id'],
            'name': plan_config.name,
            'path': input_node['path'] + [plan_config.name],
            'group': plan_config.name,
            'artifacts': input_node['artifacts'],
            'revision': input_node['revision'],
        }
        return api.submit({'node': job_node})[0]

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        if args.input_node_id:
            input_node = api.get_node(args.input_node_id)
        elif args.input_node_json:
            input_node = self._load_json(args.input_node_json)
        else:
            print("\
Invalid arguments.  Either --input-node-id or --input-node-json is required.")
            return False
        plan_config = configs['test_plans'][args.plan]
        node = self._create_node(api, input_node, plan_config)
        if args.id_only:
            print(node['_id'])
        else:
            self._print_json(node, args.indent)
        return True


class cmd_generate(APICommand):  # pylint: disable=invalid-name
    """Generate a job definition file"""
    args = APICommand.args + [
        {
            'name': '--runtime-config',
            'help': "Name of the runtime config",
        },
        {
            'name': '--platform',
            'help': "Name of the platform to run the job",
        },
    ]
    opt_args = APICommand.opt_args + [
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

    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        if args.node_id:
            job_node = api.get_node(args.node_id)
        elif args.node_json:
            job_node = self._load_json(args.node_json)
        else:
            print("\
Invalid arguments.  Either --node-id or --node-json is required.")
            return False
        plan_config = configs['test_plans'][job_node['name']]
        platform_config = configs['device_types'][args.platform]
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(runtime_config)

        # This should be part of the Runtime implementation
        params = {
            'api_config_yaml': yaml.dump(api.config),
            'name': plan_config.name,
            'revision': job_node['revision'],
            'runtime': runtime_config.lab_type,
            'runtime_image': plan_config.image,
            'tarball_url': job_node['artifacts']['tarball'],
        }
        params.update(plan_config.params)
        params.update(platform_config.params)
        job = runtime.generate(params, platform_config, plan_config)
        if args.output:
            output_file = runtime.save_file(job, args.output, params)
            print(f"Job saved in {output_file}")
        else:
            print(job)

        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("job", globals(), args)
