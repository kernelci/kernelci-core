# Copyright (C) 2022 Collabora Limited
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

import random
import re
import string
from jinja2 import Environment, FileSystemLoader
from kernelci.lab import LabAPI


class Kubernetes(LabAPI):
    RANDOM_CHARACTERS = string.ascii_lowercase + string.digits

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_path='config/kubernetes'):
        jinja2_env = Environment(loader=FileSystemLoader(templates_path))
        template_path = plan_config.get_template_path(None)
        template = jinja2_env.get_template(template_path)
        job_name = '-'.join([
            'kci', params['node_id'], params['name'][:24]
        ])
        safe_name = re.sub(r'[\:/_+=]', '-', job_name).lower()
        rand_sx = ''.join(random.sample(self.RANDOM_CHARACTERS, 8))
        k8s_job_name = '-'.join([safe_name[:(62 - len(rand_sx))], rand_sx])
        params['k8s_job_name'] = k8s_job_name
        return template.render(params)

    def job_file_name(self, params):
        return '.'.join([params['k8s_job_name'], 'yaml'])

    def submit(self, job_path, get_process=False):
        raise NotImplementedError("ToDo")


def get_api(lab, **kwargs):
    """Get a Kubernetes object"""
    return Kubernetes(lab, **kwargs)
