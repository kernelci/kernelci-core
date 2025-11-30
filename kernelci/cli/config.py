# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage the KernelCI YAML pipeline configuration"""

import os
import sys
import json

import click
import yaml

import kernelci.config
import kernelci.api.helper
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


def validate_rules(node, rules):
    """Validate if the node should be created based on the rules"""
    helper = kernelci.api.helper.APIHelper(None)
    return helper.should_create_node(rules, node)


def compare_builds(merged_data):
    """
    Compare kbuilds and print builds with identical params
    """
    result = ""
    jobs = merged_data.get("jobs")
    if not jobs:
        click.echo("No jobs found in the merged data, "
                   "maybe you need to add parameter "
                   "-c path/kernelci-pipeline/config?")
        sys.exit(1)
    kbuilds_list = []
    for job in jobs:
        if jobs[job].get("kind") == "kbuild":
            kbuilds_list.append(job)

    kbuilds_dict = {}
    for kbuild in kbuilds_list:
        params = jobs[kbuild].get("params", {})
        # Convert params to a hashable type by serializing to JSON
        key = json.dumps(params, sort_keys=True)
        if key not in kbuilds_dict:
            kbuilds_dict[key] = []
        kbuilds_dict[key].append(kbuild)

    # print builds with identical params
    for params, kbuild_list in kbuilds_dict.items():
        if len(kbuild_list) > 1:
            result += f"Params {params}: {kbuild_list},"

    return result


def forecast_tests(merged_data, kbuild, checkout):
    """
    Forecast tests for a given kbuild and checkout.
    """
    tests = []
    jobs = merged_data.get("scheduler", [])
    for job in jobs:
        kind = job.get("event", {}).get("kind")
        if kind != "kbuild":
            continue
        if job.get("event", {}).get("name") != kbuild:
            continue
        scheduler_rules = job.get("rules", [])
        job_name = job.get("job")
        job_data = merged_data.get("jobs", {}).get(job_name, {})
        job_rules = job_data.get("rules", [])
        # we might have rules in scheduler entries too
        scheduler_rules = job.get("rules", [])
        node = {
            "kind": "kbuild",
            "data": {
                "kernel_revision": {
                    "tree": checkout.get("tree"),
                    "branch": checkout.get("branch"),
                    "version": {
                        "version": 6,
                        "patchlevel": 16,
                        "extra": "-rc3-973-gb7d1bbd97f77"
                    },
                }
            },
        }
        if not validate_rules(node, job_rules) or not validate_rules(node, scheduler_rules):
            continue
        # runtime/name in scheduler
        runtime = job.get("runtime", {}).get("name")
        platforms = job.get("platforms", [])
        test_name = f"{job_name} ({runtime}) {platforms}"
        tests.append(test_name)

    return tests


# pylint: disable=too-many-branches disable=too-many-locals
def do_forecast(merged_data):
    """
    We will simulate checkout event on each tree/branch
    and try to build list of builds/tests it will run
    """
    checkouts = []
    build_configs = merged_data.get("build_configs", {})
    for bcfg in build_configs:
        data = build_configs[bcfg]
        if not data.get("architectures"):
            data["architectures"] = None
        checkouts.append(data)

    # sort checkouts by tree and branch
    checkouts.sort(key=lambda x: (x.get("tree", ""), x.get("branch", "")))

    # iterate over checkouts
    for checkout in checkouts:
        checkout["kbuilds"] = []
        # iterate over events (jobs)
        jobs = merged_data.get("scheduler", [])
        for job in jobs:
            kind = job.get("event", {}).get("kind")
            if kind != "checkout":
                continue
            job_name = job.get("job")
            job_kind = merged_data.get("jobs", {}).get(job_name, {}).get("kind")
            if job_kind == "kbuild":
                # check "params" "arch"
                job_params = merged_data.get("jobs", {}).get(job_name, {}).get("params", {})
                arch = job_params.get("arch")
                if checkout.get("architectures") and arch not in checkout.get("architectures"):
                    continue
            scheduler_rules = job.get("rules", [])
            job = merged_data.get("jobs", {}).get(job_name, {})
            job_rules = job.get("rules", [])
            node = {
                "kind": "checkout",
                "data": {
                    "kernel_revision": {
                        "tree": checkout.get("tree"),
                        "branch": checkout.get("branch"),
                        "version": {
                            "version": 6,
                            "patchlevel": 16,
                            "extra": "-rc3-973-gb7d1bbd97f77"
                        },
                    }
                },
            }
            if not validate_rules(node, job_rules) or not validate_rules(node, scheduler_rules):
                continue
            tests = forecast_tests(merged_data, job_name, checkout)
            kbuild = {
                "name": job_name,
                "tests": tests
            }
            checkout["kbuilds"].append(kbuild)
        checkout["kbuilds_identical"] = compare_builds(merged_data)

    # print the results
    for checkout in checkouts:
        print(f"Checkout: {checkout.get('tree')}:{checkout.get('branch')}")
        if checkout.get("kbuilds_identical"):
            print(f"  Identical builds: {checkout['kbuilds_identical']}")
        if checkout.get("kbuilds"):
            num_builds = len(checkout["kbuilds"])
            print(f"  Number of builds: {num_builds}")
            print("  Builds:")
            for build in checkout["kbuilds"]:
                print(f"    - {build['name']}")
                print(f"      Number of tests: {len(build.get('tests', []))}")
                for test in build.get('tests', []):
                    print(f"      - {test}")
        else:
            print("  No builds found for this checkout")


@kci_config.command
@Args.config
@Args.debug
def forecast(config, debug):
    """Forecast builds and tests for each tree/branch combination"""
    if debug:
        os.environ['KCI_DEBUG'] = '1'
    config_paths = kernelci.config.get_config_paths(config)
    if not config_paths:
        return
    data = kernelci.config.load_yaml(config_paths)
    do_forecast(data)
