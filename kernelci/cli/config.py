# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to manage the KernelCI YAML pipeline configuration"""

import json
import os
import sys

import click
import yaml
from jinja2 import Environment, FileSystemLoader

import kernelci.config

from . import Args, kci

REPORT_TEMPLATE_PATHS = [
    "config/report",
    "/etc/kernelci/config/report",
]

FORECAST_KERNEL_VERSION = {
    "version": 6,
    "patchlevel": 16,
    "extra": "-rc3-973-gb7d1bbd97f77",
}


@kci.group(name="config")
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
        "jobs",
        "runtimes",
        "scheduler",
    ]
    err = kernelci.config.validate_yaml(config, sections)
    if err:
        raise click.ClickException(err)
    if verbose:
        click.echo("YAML configuration validation succeeded.")


@kci_config.command
@click.argument("section", required=False)
@Args.config
@Args.indent
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    help="Dump recursively the contents of each entry",
)
def dump(section, config, indent, recursive):
    """Dump entries from the SECTION of the pipeline YAML configuration"""
    data = kernelci.config.load(config)
    if section:
        for step in section.split("."):
            data = (
                data.get(step, {})
                if isinstance(data, dict)
                else getattr(data, step)
            )
    if not data:
        raise click.ClickException(f"Section not found: {section}")
    if isinstance(data, dict) and not recursive:
        keys = list(sorted(data.keys()))
        _, lines = os.get_terminal_size()
        echo = click.echo_via_pager if len(keys) >= lines else click.echo
        echo("\n".join(keys))
    elif isinstance(data, (str, int, float)):
        click.echo(data)
    else:
        echo = click.echo_via_pager if recursive else click.echo
        echo(yaml.dump(data, indent=indent))


def validate_rules(node, rules):
    """Validate if the node should be created based on the rules"""
    return not evaluate_rules(rules, node)


def _find_container(field, node):
    for key, value in node.items():
        if key == field:
            return node
        if isinstance(value, dict):
            base_object = _find_container(field, value)
            if base_object:
                return base_object
    return None


def _split_rules(rules, key):
    allow = []
    allow_combos = []
    deny = []
    deny_combos = []

    for rule in rules.get(key, []):
        if ":" in rule:
            tree, branch = rule.split(":", 1)
            combo = {"tree": tree.lstrip("!"), "branch": branch}
            if tree.startswith("!"):
                deny_combos.append(combo)
            else:
                allow_combos.append(combo)
        elif rule.startswith("!"):
            deny.append(rule.lstrip("!"))
        else:
            allow.append(rule)

    return allow, allow_combos, deny, deny_combos


def _match_combo(node, combos):
    for combo in combos:
        if node["tree"] == combo["tree"] and node["branch"] == combo["branch"]:
            return combo
    return None


def _evaluate_tree_branch_rules(rules, node, prefix):
    reasons = []
    ref_base = _find_container("tree", node)
    if not ref_base:
        return reasons

    for key in ("tree", "branch"):
        if key not in rules:
            continue
        allow, allow_combos, deny, deny_combos = _split_rules(rules, key)
        if _match_combo(ref_base, allow_combos):
            break
        denied_combo = _match_combo(ref_base, deny_combos)
        if denied_combo:
            reasons.append(
                f"{prefix}: rules[{key}] rejects "
                f"{denied_combo['tree']}:{denied_combo['branch']}"
            )
            return reasons
        if ref_base[key] in deny:
            reasons.append(f"{prefix}: rules[{key}] rejects {ref_base[key]}")
            return reasons
        if not allow and allow_combos:
            reasons.append(
                f"{prefix}: rules[{key}] has tree/branch allow-list "
                f"that does not include {ref_base[key]}"
            )
            return reasons
        if allow and ref_base[key] not in allow:
            reasons.append(
                f"{prefix}: rules[{key}] allows {allow}, not {ref_base[key]}"
            )
            return reasons

    return reasons


def _evaluate_version_rule(key, rule, node, prefix):
    kver = node["data"]["kernel_revision"]["version"]
    major = kver["version"]
    minor = kver["patchlevel"]
    rule_major = rule["version"]
    rule_minor = rule["patchlevel"]
    if key.startswith("min") and (
        major < rule_major or (major == rule_major and minor < rule_minor)
    ):
        return [
            f"{prefix}: rules[{key}] requires at least "
            f"{rule_major}.{rule_minor}, got {major}.{minor}"
        ]
    if key.startswith("max") and (
        major > rule_major or (major == rule_major and minor > rule_minor)
    ):
        return [
            f"{prefix}: rules[{key}] requires at most "
            f"{rule_major}.{rule_minor}, got {major}.{minor}"
        ]
    return []


def _evaluate_list_rule(key, value, allow, deny, prefix):
    denied_values = [item for item in value if item in deny]
    if denied_values:
        return [f"{prefix}: rules[{key}] rejects {denied_values}"]
    if allow and not any(item in allow for item in value):
        return [f"{prefix}: rules[{key}] requires one of {allow}, got {value}"]
    return []


def _evaluate_scalar_rule(key, value, allow, deny, prefix):
    if value in deny:
        return [f"{prefix}: rules[{key}] rejects {value}"]
    if allow and value not in allow:
        return [f"{prefix}: rules[{key}] allows {allow}, got {value}"]
    return []


def _evaluate_field_rule(key, rule, node, prefix):
    base = _find_container(key, node)
    deny = [item.lstrip("!") for item in rule if item.startswith("!")]
    allow = [item for item in rule if not item.startswith("!")]

    if not base:
        if allow:
            return [
                f"{prefix}: rules[{key}] requires one of {allow}, "
                "but the field is missing"
            ]
        return []

    value = base[key]
    if isinstance(value, list):
        return _evaluate_list_rule(key, value, allow, deny, prefix)
    return _evaluate_scalar_rule(key, value, allow, deny, prefix)


def evaluate_rules(rules, node, prefix="rules"):
    """Return a list of reasons why *rules* reject *node*."""
    if not rules:
        return []

    reasons = _evaluate_tree_branch_rules(rules, node, prefix)
    if reasons:
        return reasons

    for key, rule in rules.items():
        if key in ("tree", "branch"):
            continue
        if key.endswith("_version"):
            reasons.extend(_evaluate_version_rule(key, rule, node, prefix))
        else:
            reasons.extend(_evaluate_field_rule(key, rule, node, prefix))

    return reasons


def make_forecast_checkout_node(checkout):
    return {
        "kind": "checkout",
        "name": "checkout",
        "data": {
            "kernel_revision": {
                "tree": checkout.get("tree"),
                "branch": checkout.get("branch"),
                "version": FORECAST_KERNEL_VERSION.copy(),
            }
        },
    }


def make_forecast_child_node(
    job_name, job_data, input_node, runtime=None, platform=None
):
    data = {
        "kernel_revision": input_node["data"]["kernel_revision"],
    }
    input_data = input_node.get("data", {})
    for field in (
        "arch",
        "compiler",
        "config_full",
        "defconfig",
        "fragments",
        "kernel_type",
    ):
        if field in input_data:
            data[field] = input_data[field]

    if job_data.get("kind") == "kbuild":
        data.update(job_data.get("params", {}))

    if runtime:
        data["runtime"] = runtime
    if platform:
        data["platform"] = platform

    return {
        "kind": job_data.get("kind"),
        "name": job_name,
        "data": data,
    }


def compare_builds(merged_data):
    """
    Compare kbuilds and print builds with identical params
    """
    result = ""
    jobs = merged_data.get("jobs")
    if not jobs:
        click.echo(
            "No jobs found in the merged data, "
            "maybe you need to add parameter "
            "-c path/kernelci-pipeline/config?"
        )
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
    kbuild_data = merged_data.get("jobs", {}).get(kbuild, {})
    checkout_node = make_forecast_checkout_node(checkout)
    kbuild_node = make_forecast_child_node(kbuild, kbuild_data, checkout_node)
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
        test_node = make_forecast_child_node(
            job_name,
            job_data,
            kbuild_node,
            runtime=job.get("runtime", {}).get("name"),
        )
        if not validate_rules(
            kbuild_node, scheduler_rules
        ) or not validate_rules(test_node, job_rules):
            continue
        # runtime/name in scheduler
        runtime = job.get("runtime", {}).get("name")
        platforms = job.get("platforms", [])
        test_name = f"{job_name} ({runtime}) {platforms}"
        tests.append(test_name)

    return tests


def get_forecast_data(merged_data):
    """
    Process merged data to get forecast of builds and tests.
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
        for scheduler_entry in jobs:
            kind = scheduler_entry.get("event", {}).get("kind")
            if kind != "checkout":
                continue
            job_name = scheduler_entry.get("job")
            job_kind = merged_data.get("jobs", {}).get(job_name, {}).get("kind")
            if job_kind == "kbuild":
                # check "params" "arch"
                job_params = (
                    merged_data.get("jobs", {})
                    .get(job_name, {})
                    .get("params", {})
                )
                arch = job_params.get("arch")
                if checkout.get("architectures") and arch not in checkout.get(
                    "architectures"
                ):
                    continue
            scheduler_rules = scheduler_entry.get("rules", [])
            job = merged_data.get("jobs", {}).get(job_name, {})
            job_rules = job.get("rules", [])
            checkout_node = make_forecast_checkout_node(checkout)
            kbuild_node = make_forecast_child_node(
                job_name,
                job,
                checkout_node,
                runtime=scheduler_entry.get("runtime", {}).get("name"),
            )
            if not validate_rules(
                checkout_node, scheduler_rules
            ) or not validate_rules(kbuild_node, job_rules):
                continue
            tests = forecast_tests(merged_data, job_name, checkout)
            kbuild = {"name": job_name, "tests": tests}
            checkout["kbuilds"].append(kbuild)
        checkout["kbuilds_identical"] = compare_builds(merged_data)

    return checkouts


def print_forecast(checkouts):
    """
    Print the forecast results to stdout.
    """
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
                for test in build.get("tests", []):
                    print(f"      - {test}")
        else:
            print("  No builds found for this checkout")


def generate_html_report(checkouts, output_dir):
    """
    Generate an HTML report for the forecast using Jinja2 template.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    jinja2_env = Environment(loader=FileSystemLoader(REPORT_TEMPLATE_PATHS))
    template = jinja2_env.get_template("forecast.jinja2")

    final_html = template.render(checkouts=checkouts)

    with open(
        os.path.join(output_dir, "index.html"), "w", encoding="utf-8"
    ) as outfile:
        outfile.write(final_html)

    print(
        f"Forecast report generated at: {os.path.join(output_dir, 'index.html')}"
    )


def _runtime_name(runtime):
    if not runtime:
        return None
    return runtime.get("name") or runtime.get("type")


def _event_source_name(event):
    if event.get("kind") == "checkout":
        return event.get("name", "checkout")
    return event.get("name")


def _node_signature(node):
    return json.dumps(node, sort_keys=True)


def _candidate_platforms(entry):
    platforms = entry.get("platforms", [])
    return platforms or [None]


def _runtime_filter_reasons(merged_data, runtime, runtime_name, runtime_filter):
    if runtime_filter and runtime_name != runtime_filter:
        return [
            f"runtime filter requests {runtime_filter}, "
            f"entry uses {runtime_name}"
        ]
    if (
        runtime.get("name")
        and merged_data.get("runtimes")
        and runtime_name not in merged_data["runtimes"]
    ):
        return [f"runtime config {runtime_name!r} is missing"]
    return []


def _kbuild_architecture_reasons(job_data, checkout):
    if job_data.get("kind") != "kbuild":
        return []
    arch = job_data.get("params", {}).get("arch")
    architectures = checkout.get("architectures")
    if architectures and arch not in architectures:
        return [
            f"checkout architecture filter {architectures} excludes "
            f"kbuild arch {arch}"
        ]
    return []


def _platform_filter_reasons(platform_name, platform_filter):
    if platform_filter and platform_name != platform_filter:
        return [
            f"platform filter requests {platform_filter}, "
            f"entry platform is {platform_name or '<none>'}"
        ]
    return []


def _forecast_child_reasons(
    merged_data, job_name, job_data, child_node, platform_name, runtime_name
):
    platforms = merged_data.get("platforms", {})
    if platform_name and platforms and platform_name not in platforms:
        return [f"platform config {platform_name!r} is missing"]
    platform_data = platforms.get(platform_name, {})
    platform_rules = platform_data.get("rules") if platform_data else None
    runtime_data = merged_data.get("runtimes", {}).get(runtime_name, {})
    runtime_rules = runtime_data.get("rules") if runtime_data else None
    reasons = []
    reasons.extend(
        evaluate_rules(
            job_data.get("rules"),
            child_node,
            prefix=f"job {job_name}",
        )
    )
    reasons.extend(
        evaluate_rules(
            platform_rules,
            child_node,
            prefix=f"platform {platform_name}",
        )
    )
    reasons.extend(
        evaluate_rules(
            runtime_rules,
            child_node,
            prefix=f"runtime {runtime_name}",
        )
    )
    return reasons


def _evaluate_platform_candidate(
    merged_data,
    entry,
    input_node,
    job_data,
    platform_name,
    platform_filter,
    runtime_name,
):
    job_name = entry.get("job")
    reasons = _platform_filter_reasons(platform_name, platform_filter)
    if reasons:
        return None, reasons

    child_node = make_forecast_child_node(
        job_name,
        job_data,
        input_node,
        runtime=runtime_name,
        platform=platform_name,
    )
    child_reasons = _forecast_child_reasons(
        merged_data, job_name, job_data, child_node, platform_name, runtime_name
    )
    if child_reasons:
        return None, [
            f"{platform_name or '<no platform>'}: {reason}"
            for reason in child_reasons
        ]
    return child_node, []


def evaluate_forecast_entry(
    merged_data,
    entry,
    input_node,
    checkout,
    *,
    platform_filter=None,
    runtime_filter=None,
):
    """Return possible child nodes and blocked reasons for a scheduler entry."""
    reasons = []
    job_name = entry.get("job")
    job_data = merged_data.get("jobs", {}).get(job_name)
    runtime = entry.get("runtime", {})
    runtime_name = _runtime_name(runtime)

    reasons.extend(
        _runtime_filter_reasons(
            merged_data, runtime, runtime_name, runtime_filter
        )
    )
    if reasons:
        return [], reasons

    if not job_data:
        return [], [f"job config {job_name!r} is missing"]

    reasons.extend(_kbuild_architecture_reasons(job_data, checkout))
    reasons.extend(
        evaluate_rules(
            entry.get("rules"),
            input_node,
            prefix=f"scheduler entry for {job_name}",
        )
    )
    if reasons:
        return [], reasons

    nodes = []
    for platform_name in _candidate_platforms(entry):
        child_node, platform_reasons = _evaluate_platform_candidate(
            merged_data,
            entry,
            input_node,
            job_data,
            platform_name,
            platform_filter,
            runtime_name,
        )
        if platform_reasons:
            reasons.extend(platform_reasons)
            continue
        nodes.append(child_node)

    return nodes, reasons


def build_forecast_graph(merged_data, checkout):
    """Build a forward forecast graph for one checkout tree/branch."""
    root_node = make_forecast_checkout_node(checkout)
    nodes = {"checkout": [root_node]}
    signatures = {"checkout": {_node_signature(root_node)}}
    scheduler_entries = merged_data.get("scheduler", [])

    changed = True
    while changed:
        changed = False
        for entry in scheduler_entries:
            source_name = _event_source_name(entry.get("event", {}))
            if not source_name:
                continue
            for input_node in nodes.get(source_name, []):
                child_nodes, _ = evaluate_forecast_entry(
                    merged_data, entry, input_node, checkout
                )
                for child_node in child_nodes:
                    job_name = child_node["name"]
                    node_sig = _node_signature(child_node)
                    job_sigs = signatures.setdefault(job_name, set())
                    if node_sig in job_sigs:
                        continue
                    job_sigs.add(node_sig)
                    nodes.setdefault(job_name, []).append(child_node)
                    changed = True

    return nodes


def _matching_target_nodes(nodes, job_name, platform=None, runtime=None):
    matches = []
    for node in nodes.get(job_name, []):
        data = node.get("data", {})
        if platform and data.get("platform") != platform:
            continue
        if runtime and data.get("runtime") != runtime:
            continue
        matches.append(node)
    return matches


def _describe_node(node):
    data = node.get("data", {})
    parts = [node.get("name")]
    if data.get("runtime"):
        parts.append(f"runtime={data['runtime']}")
    if data.get("platform"):
        parts.append(f"platform={data['platform']}")
    return " ".join(parts)


def _explain_source(
    merged_data,
    checkout,
    nodes,
    job_name,
    *,
    seen=None,
    indent="    ",
):
    seen = seen or set()
    if job_name in seen:
        return [f"{indent}- {job_name}: dependency cycle detected"]
    seen.add(job_name)

    if job_name in nodes:
        return [f"{indent}- {job_name}: scheduled"]

    lines = [f"{indent}- {job_name}: missing"]
    entries = [
        entry
        for entry in merged_data.get("scheduler", [])
        if entry.get("job") == job_name
    ]
    if not entries:
        lines.append(f"{indent}  no scheduler entry creates this job")
        return lines

    for entry in entries:
        source_name = _event_source_name(entry.get("event", {}))
        lines.append(f"{indent}  needs input: {source_name or '<unnamed>'}")
        if source_name:
            lines.extend(
                _explain_source(
                    merged_data,
                    checkout,
                    nodes,
                    source_name,
                    seen=seen.copy(),
                    indent=indent + "  ",
                )
            )
    return lines


def _forecast_checkout(merged_data, tree, branch):
    for build_config in merged_data.get("build_configs", {}).values():
        if (
            build_config.get("tree") == tree
            and build_config.get("branch") == branch
        ):
            return build_config.copy()
    return {"tree": tree, "branch": branch}


def _scheduler_entries_for_job(merged_data, job_name):
    return [
        entry
        for entry in merged_data.get("scheduler", [])
        if entry.get("job") == job_name
    ]


def _format_forecast_header(job_name, tree, branch, result, platform, runtime):
    lines = [
        f"Forecast explanation for {job_name} on {tree}:{branch}",
        f"Result: {result}",
    ]
    if platform:
        lines.append(f"Expected platform: {platform}")
    if runtime:
        lines.append(f"Expected runtime: {runtime}")
    return lines


def _format_matching_nodes(matches):
    lines = ["Matching forecast nodes:"]
    lines.extend(f"  - {_describe_node(node)}" for node in matches)
    return lines


def _format_missing_source(merged_data, checkout, nodes, source_name):
    lines = ["    blocked: required input was not forecast"]
    if source_name:
        lines.extend(_explain_source(merged_data, checkout, nodes, source_name))
    return lines


def _format_blocked_entry(
    merged_data,
    checkout,
    entry,
    source_nodes,
    platform,
    runtime,
):
    blocked = []
    for source_node in source_nodes:
        child_nodes, reasons = evaluate_forecast_entry(
            merged_data,
            entry,
            source_node,
            checkout,
            platform_filter=platform,
            runtime_filter=runtime,
        )
        if child_nodes:
            continue
        blocked.extend(reasons)
    if not blocked:
        return ["    blocked: no matching output node was created"]
    return [f"    blocked: {reason}" for reason in sorted(set(blocked))]


def _format_candidate_entries(
    merged_data,
    checkout,
    nodes,
    entries,
    platform,
    runtime,
):
    lines = ["Candidate scheduler entries:"]
    for index, entry in enumerate(entries, start=1):
        event = entry.get("event", {})
        source_name = _event_source_name(event)
        lines.append(
            f"  - entry {index}: needs "
            f"{event.get('kind')}:{source_name or '<unnamed>'}"
        )
        source_nodes = nodes.get(source_name, []) if source_name else []
        if source_nodes:
            lines.extend(
                _format_blocked_entry(
                    merged_data,
                    checkout,
                    entry,
                    source_nodes,
                    platform,
                    runtime,
                )
            )
        else:
            lines.extend(
                _format_missing_source(
                    merged_data, checkout, nodes, source_name
                )
            )
    return lines


def _format_reverse_graph(
    merged_data, checkout, nodes, job_name, platform, runtime
):
    lines = ["Reverse graph:"]
    if job_name in nodes and (platform or runtime):
        lines.append(
            f"    - {job_name}: scheduled in the broader forecast, "
            "but not with the requested platform/runtime filters"
        )
    else:
        lines.extend(_explain_source(merged_data, checkout, nodes, job_name))
    return lines


def explain_forecast_job(
    merged_data,
    job_name,
    tree,
    branch,
    *,
    platform=None,
    runtime=None,
):
    """Return printable lines explaining if a job is forecast for a checkout."""
    checkout = _forecast_checkout(merged_data, tree, branch)
    nodes = build_forecast_graph(merged_data, checkout)
    matches = _matching_target_nodes(nodes, job_name, platform, runtime)
    result = "scheduled" if matches else "not scheduled"
    lines = _format_forecast_header(
        job_name, tree, branch, result, platform, runtime
    )
    if matches:
        lines.extend(_format_matching_nodes(matches))
        return lines

    entries = _scheduler_entries_for_job(merged_data, job_name)
    if not entries:
        lines.append(f"  - no scheduler entry creates {job_name}")
        return lines

    lines.extend(
        _format_candidate_entries(
            merged_data, checkout, nodes, entries, platform, runtime
        )
    )
    lines.extend(
        _format_reverse_graph(
            merged_data, checkout, nodes, job_name, platform, runtime
        )
    )
    return lines


@kci_config.command
@Args.config
@Args.debug
@click.option(
    "--html",
    type=click.Path(),
    help="Generate HTML report in the specified directory",
)
@click.option(
    "--explain-job",
    help="Explain why a specific job is or is not in the forecast",
)
@click.option("--tree", help="Tree name to use with --explain-job")
@click.option("--branch", help="Branch name to use with --explain-job")
@click.option("--platform", help="Expected platform for --explain-job")
@click.option("--runtime", help="Expected runtime for --explain-job")
def forecast(config, debug, html, explain_job, tree, branch, platform, runtime):
    """Forecast builds and tests for each tree/branch combination"""
    if debug:
        os.environ["KCI_DEBUG"] = "1"
    config_paths = kernelci.config.get_config_paths(config)
    if not config_paths:
        return
    data = kernelci.config.load_yaml(config_paths)

    if explain_job:
        if not tree or not branch:
            raise click.ClickException(
                "--tree and --branch are required with --explain-job"
            )
        for line in explain_forecast_job(
            data,
            explain_job,
            tree,
            branch,
            platform=platform,
            runtime=runtime,
        ):
            click.echo(line)
        return

    checkouts = get_forecast_data(data)

    if html:
        generate_html_report(checkouts, html)
    else:
        print_forecast(checkouts)
