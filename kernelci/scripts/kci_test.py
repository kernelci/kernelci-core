#!/usr/bin/env python3
#
# Copyright (C) 2019 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import glob
import json
import os
import re
import sys
from pathlib import Path
import requests
import yaml

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from kernelci.legacy.cli import Args, Command, parse_opts  # noqa: E402
import kernelci  # noqa: E402
import kernelci.legacy.config.test  # noqa: E402
import kernelci.build  # noqa: E402
import kernelci.runtime  # noqa: E402
import kernelci.legacy  # noqa: E402
import kernelci.test  # noqa: E402

RELEASE_RE = re.compile(r'(.*)([0-9.]{10})(.*)')


# -----------------------------------------------------------------------------
# Commands
#

class cmd_validate(Command):
    help = "Validate the YAML configuration"
    opt_args = [Args.verbose]

    def __call__(self, configs, args):
        # ToDo: Use jsonschema

        entries = [
            'device_types',
            'file_system_types',
            'test_plans',
            'runtimes',
        ]
        err = kernelci.config.validate_yaml(args.yaml_config, entries)
        if err:
            print(err)
            return False

        test_config_devices = list(
            str(config.device_type) for config in configs['test_configs']
        )
        for device_type in configs['device_types'].keys():
            if device_type not in test_config_devices:
                print("Device type has no test config: {}".format(device_type))
                return False

        for config in configs['test_configs']:
            err = kernelci.sort_check(config.test_plans.keys())
            if err:
                print("Plans broken order for {}: '{}' before '{}'".format(
                    config.device_type, err[0], err[1]))
                return False

        return True


def _iterate_fs_configs(file_systems_config):
    for fs, config in file_systems_config.items():
        fs_parts = fs.split('_')
        if fs_parts[0] == 'debian':
            name = fs_parts[1]
            root_type = fs_parts[2]
        elif fs_parts[0].startswith('buildroot'):
            name = fs_parts[0]
            root_type = fs_parts[1]
        else:
            continue
        yield fs, config, name, root_type


def _check_rootfs_urls(fs_config, rootfs_config, root_type, verbose):
    url_formats = [
        url_fmt for url_fmt in (
            fs_config.get_url_format(fmt_type)
            for fmt_type in set({root_type}).union({'nfs', 'ramdisk'})
        ) if url_fmt
    ]
    for arch in rootfs_config.arch_list:
        for url_format in url_formats:
            url = url_format.format(arch=arch)
            resp = requests.head(url)
            if verbose:
                print(f"  {resp.status_code} {url}")
            resp.raise_for_status()


def _get_fs_config_dicts(config, release):
    old_config_dict = config.to_dict()
    new_config_dict = old_config_dict.copy()
    for image in ['ramdisk', 'nfs']:
        path = old_config_dict.get(image)
        if path:
            p_start, p_rel, p_end = RELEASE_RE.match(path).groups()
            new_config_dict[image] = ''.join([p_start, release, p_end])
    return old_config_dict, new_config_dict


def _check_new_config_urls(new_config, rootfs, root_type, verbose):
    try:
        _check_rootfs_urls(new_config, rootfs, root_type, verbose)
        if verbose:
            print("  OK")
        return True
    except Exception as e:
        if verbose:
            print(f"  FAIL: {e}")
        return False


class cmd_validate_rootfs_urls(Command):
    help = "Check that all the rootfs URLs are valid"
    opt_args = [Args.verbose]

    def __call__(self, config_data, args, **kwargs):
        rootfs_configs = config_data['rootfs_configs']
        fs_configs = config_data['file_systems']
        for fs, config, name, root_type in _iterate_fs_configs(fs_configs):
            if args.verbose:
                print(fs)
            rootfs_config = rootfs_configs.get(name)
            _check_rootfs_urls(config, rootfs_config, root_type, args.verbose)
        return True


class cmd_update_rootfs_urls(Command):
    help = "Update the rootfs URLs for those that are valid"
    args = [
        {
            'name': '--release',
            'help': 'Release name used in the path e.g. 20220913.0',
        },
        {
            'name': '--output',
            'help': 'Ouput YAML file name to store the new configuration',
        },
    ]
    opt_args = [Args.verbose]

    def __call__(self, config_data, args):
        fs_types = config_data['file_system_types']
        fs_configs = config_data['file_systems']
        rootfs_configs = config_data['rootfs_configs']
        new_configs = {}
        for fs, config, name, root_type in _iterate_fs_configs(fs_configs):
            if args.verbose:
                print(fs)
            rootfs_config = rootfs_configs.get(name)
            old_dict, new_dict = _get_fs_config_dicts(config, args.release)
            new_config = kernelci.config.test.RootFS.from_yaml(
                fs_types, new_dict
            )
            new_configs[fs] = (
                new_dict if _check_new_config_urls(
                    new_config, rootfs_config, root_type, args.verbose)
                else old_dict
            )
        if args.verbose:
            print(f"Writing output to {args.output}")
        with open(args.output, 'w') as output_file:
            output_file.write(f"# Automatically generated ({args.release})\n")
            data = {'file_systems': new_configs}
            yaml.dump(data, output_file, default_flow_style=False)
        return True


class cmd_list_jobs(Command):
    help = "List all the jobs that need to be run for a given build and lab"
    args = [Args.runtime_config]
    opt_args = [Args.user, Args.runtime_token, Args.runtime_json,
                Args.build_output, Args.install_path]

    def __call__(self, configs, args):
        path_args = (args.build_output, args.install_path)
        if not any(path_args) or all(path_args):
            print("Either --build-output or --install-path is required")
            return False

        install = (
            args.install_path if args.install_path else
            kernelci.build.Step.get_install_path(None, args.build_output)
        )
        meta = kernelci.build.Metadata(install)

        if meta.get('bmeta', 'build', 'status') != "PASS":
            return True

        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, args.user, args.runtime_token
        )
        if args.runtime_json:
            runtime.import_devices(args.runtime_json)
        configs = kernelci.test.match_configs(
            configs['test_configs'], meta, runtime_config)
        jobs = list()
        for device_type, plan in configs:
            if not runtime.device_type_online(device_type):
                continue
            jobs.append((device_type.name, plan.name))

        for job in sorted(jobs):
            print(' '.join(job))

        return True


class cmd_list_plans(Command):
    help = "List all the existing test plan names"

    def __call__(self, configs, args):
        plans = set(plan.name
                    for plan in list(configs['test_plans'].values()))
        for plan in sorted(plans):
            print(plan)
        return True


class cmd_list_labs(Command):
    help = "List all the existing lab names"

    def __call__(self, configs, args):
        for lab in sorted(configs['runtimes'].keys()):
            print(lab)
        return True


class cmd_get_lab_info(Command):
    help = "Get the information about a lab into a JSON file"
    args = [Args.runtime_config, Args.runtime_json]
    opt_args = [Args.user, Args.runtime_token]

    def __call__(self, configs, args):
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, args.user, args.runtime_token
        )
        data = {
            'lab': runtime_config.name,
            'lab_type': runtime_config.lab_type,
            'url': runtime_config.url,
            'devices': runtime.devices,
        }
        dir = os.path.dirname(args.runtime_json)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
        with open(args.runtime_json, 'w') as json_file:
            json.dump(data, json_file, indent=4, sort_keys=True)
        return True


class cmd_generate(Command):
    help = "Generate the job definition for a given build"
    args = [Args.runtime_config, kernelci.legacy.Args.storage]
    opt_args = [Args.plan, Args.target, Args.output,
                Args.build_output, Args.install_path,
                Args.runtime_json, Args.user, Args.runtime_token,
                Args.db_config, Args.callback_id, Args.callback_dataset,
                Args.callback_type, Args.callback_url, Args.mach,
                Args.device_id]

    def __call__(self, configs, args):
        if args.callback_id and not args.callback_url:
            print("--callback-url is required with --callback-id")
            return False

        path_args = (args.build_output, args.install_path)
        if not any(path_args) or all(path_args):
            print("Either --build-output or --install-path is required")
            return False

        install = (
            args.install_path
            or kernelci.build.Step.get_install_path(None, args.build_output)
        )
        meta = kernelci.build.Metadata(install)

        if meta.get('bmeta', 'build', 'status') != "PASS":
            return True

        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, args.user, args.runtime_token
        )
        if args.runtime_json:
            runtime.import_devices(args.runtime_json)
        if args.target and args.plan:
            device_config = configs['device_types'][args.target]
            plan_config = configs['test_plans'][args.plan]
            jobs_list = [(device_config, plan_config)]
        else:
            jobs_list = []
            test_configs = kernelci.test.match_configs(
                configs['test_configs'], meta, runtime_config)
            for device_config, plan_config in test_configs:
                if not runtime.device_type_online(device_config):
                    continue
                if args.target and device_config.name != args.target:
                    continue
                if args.plan and plan_config.name != args.plan:
                    continue
                if args.mach and device_config.mach != args.mach:
                    continue
                jobs_list.append((device_config, plan_config))

        callback_opts = {
            'id': args.callback_id,
            'dataset': args.callback_dataset or 'all',
            'type': args.callback_type or 'kernelci',
            'url': args.callback_url,
        }
        db_config = (
            configs['db_configs'][args.db_config] if args.db_config else None
        )
        if args.output and not os.path.exists(args.output):
            os.makedirs(args.output)
        for device_config, plan_config in jobs_list:
            params = kernelci.test.get_params(
                meta, device_config, plan_config, args.storage,
                args.device_id)
            job = runtime.generate(
                params, device_config, plan_config, callback_opts
            )
            if job is None:
                print("Failed to generate the job definition")
                return False
            if args.output:
                output_file = runtime.save_file(job, args.output, params)
                if output_file is None:
                    print("Failed to save the job definition, file collision")
                    return False
                print(output_file)
            else:
                print("# Job: {}".format(params['name']))
                print(job)
        return True


class cmd_submit(Command):
    help = "Submit job definitions to a runtime environment"
    args = [Args.runtime_config, Args.user, Args.runtime_token, Args.jobs]

    def __call__(self, configs, args):
        runtime_config = configs['runtimes'][args.runtime_config]
        runtime = kernelci.runtime.get_runtime(
            runtime_config, args.user, args.runtime_token
        )
        job_paths = glob.glob(args.jobs)
        res = True
        for path in job_paths:
            if not os.path.isfile(path):
                continue
            try:
                job_id = runtime.submit(path)
                print("{} {}".format(job_id, path))
            except requests.exceptions.HTTPError as e:
                print(f'HTTPError: {e}')
                r = e.response
                if r.headers.get('content-type') == 'application/json':
                    try:
                        jobj = json.loads(r.text)
                        if jobj is not None and "message" in jobj:
                            print(jobj["message"], file=sys.stderr)
                        else:
                            print(json.dumps(jobj), file=sys.stderr)
                    except json.decoder.JSONDecodeError as e:
                        print(f'Broken json: {r.text}', file=sys.stderr)
                else:
                    print(f'Reply body: {r.text}', file=sys.stderr)
                res = False
            except Exception as e:
                print("ERROR {}: {}".format(path, e), file=sys.stderr)
                res = False
        return res


# -----------------------------------------------------------------------------
# Main
#

def main():
    opts = parse_opts("kci_test", globals())
    configs = kernelci.config.load(opts.get_yaml_configs())
    status = opts.command(configs, opts)
    sys.exit(0 if status is True else 1)


if __name__ == '__main__':
    main()
