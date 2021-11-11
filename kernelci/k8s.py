# Copyright (C) 2021 Arm
# Author: Mark Brown <broonie@kernel.org>
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

import os
import pygit2
import re
import sys
import time
import yaml

from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config, utils

"""Interaction with a Kubernetes cluster"""


class k8s:
    def start_build(self, kdir, tree, branch, config, since=None, outdir=None):
        """Generate and schedule a build job"""

        arch, config_name, build_env = config

        git = pygit2.Repository(kdir)
        if not since:
            since = tree.name + "/" + branch + "~"
        since, since_ref = git.resolve_refish(since)
        head, head_ref = git.resolve_refish(tree.name + "/" + branch)
        walker = git.walk(head.id, pygit2.GIT_SORT_REVERSE)
        walker.hide(since.id)
        commits = []
        for commit in walker:
            # Ideally query the API to see if we built this already?
            commits.append(commit)

        # Work out a job name
        d = config_name.split("+")
        defconfig = d[0]
        frag = None
        if len(d) > 1:
            frag = d[1]

        # Include the HEAD commit hash to deduplicate the job name - should
        # check if the build was already done for another tree (or add the
        # tree name)
        job_name = "build-{}-{}-{}-{}".format(build_env, arch,
                                              config_name, head.id)

        if frag:
            frag = os.path.splitext(os.path.basename(frag))[0]
            job_name += "-{}".format(frag)

        # Munge the toolchain and environment to a container
        if re.match("^clang", build_env):
            build_container = build_env
        else:
            if arch == "i386":
                build_container = build_env + "_x86"
            elif arch == "x86_64":
                build_container = build_env + "_x86"
            else:
                build_container = build_env + "_" + arch

        # job name can only have '-'
        job_name = re.sub("[\\.:/_+=]", "-", job_name).lower()

        # k8s limits job-name to max 63 chars (and be sure it doesn't
        # end with '-')
        job_name = job_name[0:63].rstrip("-")

        # Scale the job based on cluster node size and defconfig, ideally
        # this would come from a configuration file rather than being hard
        # coded numbers/configs.
        cpu_limit = self.max_cpus
        if defconfig == "allnoconfig":
            cpu_limit = min(cpu_limit, 4)
        elif (defconfig != "allyesconfig") & (defconfig != "allmodconfig"):
            cpu_limit = min(cpu_limit, 16)

        # VMs tend to have loads of RAM, default to 1G per CPU
        mem_request = "{}Gi".format(cpu_limit)

        # Request a little under what we actually want to help
        # scheduling since some CPU will be allocated to admin
        # for the nodes.
        if cpu_limit < 8:
            cpu_request = cpu_limit * 0.875
        else:
            cpu_request = cpu_limit - 0.9

        # Collect all the global substitutions into a dict
        params = {
            "arch": arch,
            "base_container": "kernelci/" + "build-base",
            "build_config": "kernelci",
            "build_container": "kernelci/" + build_container,
            "build_environment": build_env,
            "commit_count": len(commits),
            "config_name": config_name,
            "cpu_limit": cpu_limit,
            "cpu_request": cpu_request,
            "git_url": tree.url,
            "git_branch": branch,
            "job_name": job_name,
            "kernel_tarball": "FIXME",
            "kernelci_core_repo": "https://github.com/kernelci/kernelci-core",
            "kernelci_core_branch": "main",
            "mem_request": mem_request,
        }

        env = Environment(
            loader=FileSystemLoader(["config/k8s"]),
            extensions=["jinja2.ext.do"]
        )

        # Generate the build commands, one set per commit
        build_commands = ""
        build_params = params

        for commit in commits:
            build_params["commit_id"] = commit.id
            build_params["git_describe"] = git.describe(commit)
            verbose = git.describe(commit, always_use_long_format=True)
            build_params["git_describe_verbose"] = verbose

            if len(commits) > 1:
                checkout_template = env.get_template("build-checkout.jinja2")
                build_commands += checkout_template.render(build_params)

            step_template = env.get_template("build-step.jinja2")
            build_commands = "\n" + build_commands
            build_render = step_template.render(build_params)
            build_commands = build_commands + build_render

        params["build_commands"] = build_commands

        # Get the base build template
        template = env.get_template("build-template.jinja2")
        job_yaml = template.render(params)
        job_dict = yaml.safe_load(job_yaml)

        # Insert an initContainer to fetch the source
        # TODO: check if we can talk to storage and fall back to git
        if len(commits) > 1:
            fetch_template = "build-fetch-git.jinja2"
        else:
            fetch_template = "build-fetch-tar.jinja2"

        init_containers = job_dict["spec"]["template"]["spec"].setdefault(
            "initContainers", []
        )
        template = env.get_template(fetch_template)
        fetch_yaml = template.render(params)
        fetch_dict = yaml.safe_load(fetch_yaml)
        init_containers.extend(fetch_dict)

        # Everything ready, dump a copy if requested and submit
        if outdir:
            f = outdir + "/" + job_name + ".yaml"
            fp = open(f, "w")
            fp.write(yaml.dump(job_dict))
            fp.close()
            print("Wrote", job_name, "to", f)

        try:
            k8s_client = client.ApiClient()
            utils.create_from_dict(k8s_client, data=job_dict)

            # TODO: register the jobs with the API (or something) so we
            # can follow the status of in progress builds.
            print("Scheduled", job_name, "for", cpu_limit, "CPUs")
        except utils.FailToCreateError as e:
            print("Failed to create job", job_name, ":", e)
            sys.exit(1)

        return True

    def __init__(self, context=None):
        # If no context is specified use the default k8s has
        if not context:
            contexts, active_context = config.list_kube_config_contexts()
            context = active_context["name"]

        print("Using Kubernetes context:", context)

        retries = 3
        while retries:
            try:
                config.load_kube_config(context=context)
                break
            except (TypeError, config.ConfigException) as e:
                print("WARNING: unable to load context", context, e)
                time.sleep(1)
                retries = retries - 1
                if retries == 0:
                    print("ERROR: unable to load context", context)
                    sys.exit(1)

        # Figure out how big a job we can allocate, assume whole capacity
        # of the largest node less some for admin.  This assumes that
        # the cluster will always keep at least one of the largest nodes
        # active, will need revisiting if that's not the case.
        self.v1_api = client.CoreV1Api()
        node_list = self.v1_api.list_node()
        self.max_cpus = 0
        for node in node_list.items:
            cpu = int(node.status.capacity["cpu"])
            if cpu > self.max_cpus:
                self.max_cpus = cpu

        if self.max_cpus < 32:
            self.max_cpus = self.max_cpus - 1
        else:
            self.max_cpus = self.max_cpus - 2

        print("Maximum CPUs per job:", self.max_cpus)
