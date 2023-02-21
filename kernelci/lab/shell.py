# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from kernelci.lab import Runtime


class Shell(Runtime):
    DEFAULT_TEMPLATE_PATHS = ['config/runtime', '/etc/kernelci/runtime']

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_paths=None):
        if templates_paths is None:
            templates_paths = self.DEFAULT_TEMPLATE_PATHS
        jinja2_env = Environment(loader=FileSystemLoader(templates_paths))
        template_path = plan_config.get_template_path(None)
        template = jinja2_env.get_template(template_path)
        return template.render(params)

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path):
        return subprocess.Popen(job_path)


def get_runtime(runtime_config, **kwargs):
    """Get a Shell runtime object"""
    return Shell(runtime_config, **kwargs)
