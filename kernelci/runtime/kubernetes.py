# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import kubernetes
import random
import re
import string
from jinja2 import Environment, FileSystemLoader
from kernelci.runtime import Runtime


class Kubernetes(Runtime):
    DEFAULT_TEMPLATE_PATHS = ['config/runtime', '/etc/kernelci/runtime']
    RANDOM_CHARACTERS = string.ascii_lowercase + string.digits

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_paths=None):
        if templates_paths is None:
            templates_paths = self.DEFAULT_TEMPLATE_PATHS
        jinja2_env = Environment(loader=FileSystemLoader(templates_paths))
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
        kubernetes.config.load_kube_config(context=self.config.context)
        client = kubernetes.client.ApiClient()
        return kubernetes.utils.create_from_yaml(client, job_path)


def get_runtime(runtime_config, **kwargs):
    """Get a Kubernetes runtime object"""
    return Kubernetes(runtime_config, **kwargs)
