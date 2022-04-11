# Copyright (C) 2021, 2022 Collabora Limited
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

import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from kernelci.lab import LabAPI


class Shell(LabAPI):

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_path='config/scripts',
                 db_config=None):
        jinja2_env = Environment(loader=FileSystemLoader(templates_path))
        template_path = plan_config.get_template_path(None)
        template = jinja2_env.get_template(template_path)
        if db_config:
            params['db_config_yaml'] = db_config.to_yaml()
        return template.render(params)

    def save_file(self, *args, **kwargs):
        output_file = super().save_file(*args, **kwargs)
        os.chmod(output_file, 0o775)
        return output_file

    def submit(self, job_path, get_process=False):
        process = subprocess.Popen(job_path)
        return process if get_process else process.pid


def get_api(lab, **kwargs):
    """Get a Shell object"""
    return Shell(lab, **kwargs)
