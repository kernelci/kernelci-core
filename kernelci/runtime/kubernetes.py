# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Kubernetes runtime implementation"""

import random
import re
import string
import os

import kubernetes
from . import Runtime


class Kubernetes(Runtime):
    """Runtime implementation to run jobs in a Kubernetes cluster

    This Runtime implementation generates a Kubernetes YAML job definition and
    submits it or "applies" it in a cluster.
    """

    JOB_NAME_CHARACTERS = string.ascii_lowercase + string.digits

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kcontext = None

    @classmethod
    def _get_job_file_name(cls, params):
        return '.'.join([params['k8s_job_name'], 'yaml'])

    def generate(self, job, params):
        template = self._get_template(job.config)
        job_name = '-'.join(['kci', job.node['id'], job.name[:24]])
        safe_name = re.sub(r'[\:/_+=]', '-', job_name).lower()
        rand_sx = ''.join(random.sample(self.JOB_NAME_CHARACTERS, 8))
        k8s_job_name = '-'.join([safe_name[:(62 - len(rand_sx))], rand_sx])
        instance = os.getenv('KCI_INSTANCE', 'prod')
        if instance == 'prod':
            params['k8s_api_key'] = 'kci-api-jwt-early-access'
        else:
            params['k8s_api_key'] = 'kci-api-jwt-staging'
        params['k8s_job_name'] = k8s_job_name
        return template.render(params)

    def submit(self, job_path):
        # if context is array, pick any random context to load-balance
        if isinstance(self.config.context, list):
            self.kcontext = random.choice(self.config.context)
        else:
            self.kcontext = self.config.context
        kubernetes.config.load_kube_config(context=self.kcontext)
        client = kubernetes.client.ApiClient()
        return kubernetes.utils.create_from_yaml(client, job_path)

    def get_job_id(self, job_object):
        return job_object[0][0].metadata.labels['job-name']

    def get_context(self):
        """Get kubernetes cluster name the job submitted to"""
        return self.kcontext

    def wait(self, job_object):
        watch = kubernetes.watch.Watch()
        core_v1 = kubernetes.client.CoreV1Api()
        job_name = job_object[0][0].metadata.labels['job-name']
        for event in watch.stream(
                func=core_v1.list_namespaced_pod, namespace='default'):
            if event['type'] != 'MODIFIED':
                continue
            if job_name not in event['object'].metadata.name:
                continue
            state = event['object'].status.container_statuses[0].state
            if not state.terminated:
                continue
            return 0 if state.terminated.reason == 'Completed' else 1


def get_runtime(runtime_config, **kwargs):
    """Get a Kubernetes runtime object"""
    return Kubernetes(runtime_config, **kwargs)
