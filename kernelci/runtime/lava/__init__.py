# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>

# pylint: disable=all

from collections import namedtuple
import time
import requests
import yaml
from urllib.parse import urljoin
from jinja2 import Environment, FileSystemLoader
import os
from kernelci.runtime import add_kci_raise, Runtime


class LavaRuntime(Runtime):
    LAVA_TEMPLATE_PATHS = ['config/lava', '/etc/kernelci/lava']

    def generate(self, params, device_config, plan_config,
                 templates_paths=None, callback_opts=None):
        if templates_paths is None:
            templates_paths = self.LAVA_TEMPLATE_PATHS
        short_template_file = plan_config.get_template_path(
            device_config.boot_method)
        base_name = params['base_device_type']
        priority = self._get_priority(plan_config)
        params.update({
            'queue_timeout': self.config.queue_timeout,
            'lab_name': self.config.name,
            'base_device_type': self._alias_device_type(base_name),
            'priority': priority,
        })
        if callback_opts:
            self._add_callback_params(params, callback_opts)
        jinja2_env = Environment(loader=FileSystemLoader(templates_paths),
                                 extensions=["jinja2.ext.do"])
        add_kci_raise(jinja2_env)
        template = jinja2_env.get_template(short_template_file)
        data = template.render(params)
        return data

    def submit(self, job_path):
        with open(job_path, 'r') as job_file:
            job = job_file.read()
            job_id = self._submit(job)
            return job_id

    def job_file_name(self, params):
        return '.'.join([params['name'], 'yaml'])

    def get_job_id(self, job_object):
        return job_object

    def _get_priority(self, plan_config):
        # Scale the job priority (from 0-100) within the available levels
        # for the lab, or use the lowest by default.
        priority = plan_config.params.get('priority', 20)
        if self.config.priority:
            priority = int(priority * self.config.priority / 100)
        elif (self.config.priority_max is not None and
              self.config.priority_min is not None):
            prio_range = self.config.priority_max - self.config.priority_min
            prio_min = self.config.priority_min
            priority = int((priority * prio_range / 100) + prio_min)
        return priority

    def _add_callback_params(self, params, opts):
        callback_id = opts.get('id')
        if not callback_id:
            return
        callback_type = opts.get('type')
        if callback_type == 'kernelci':
            lava_cb = 'boot' if params['plan'] == 'boot' else 'test'
            # ToDo: consolidate this to just have to pass the callback_url
            params['callback_name'] = '/'.join(['lava', lava_cb])
        params.update({
            'callback': callback_id,
            'callback_url': opts['url'],
            'callback_dataset': opts['dataset'],
            'callback_type': callback_type,
        })


class LAVA(Runtime):
    """Runtime implementation to run jobs in a LAVA lab

    LAVA is a framework for running tests on real hardware or QEMU.  This
    provides the basic features needed to generate a job defintion, submit it
    and wait for the job to complete.

    This currently only supports the REST API v0.2 and doesn't look for online
    devices or aliases.  It also doesn't take into account the callback
    parameters so results can't be sent to the API yet.  It requiers an API
    token to be provided to the constructor.  The user name is not used.
    """
    API_VERSION = 'v0.2'
    RestAPIServer = namedtuple('RestAPIServer', ['url', 'session'])

    def __init__(self, configs, **kwargs):
        super().__init__(configs, **kwargs)
        self._server = self._connect()

    def generate(self, job, params):
        template = self._get_template(job.config)
        return template.render(params)

    def submit(self, job_path):
        with open(job_path, 'r', encoding='utf-8') as job_file:
            job = job_file.read()
            job_id = self._submit(job)
            return job_id

    def get_job_id(self, job_object):
        job_id = int(job_object)
        return job_id

    def wait(self, job_object):
        job_id = int(job_object)
        job_url = urljoin(self._server.url, '/'.join(['jobs', str(job_id)]))
        while True:
            resp = self._server.session.get(job_url)
            resp.raise_for_status()
            data = resp.json()
            if data['state'] == 'Finished':
                health = data['health']
                return 0 if health == 'Complete' else 1
            time.sleep(3)

    def _connect(self):
        rest_url = f'{self.config.url}/api/{self.API_VERSION}/'
        rest_api = self.RestAPIServer(rest_url, requests.Session())
        rest_api.session.params = {'format': 'json', 'limit': '256'}
        rest_api.session.headers = {
            'authorization': f'Token {self._token}',
            'content-type': 'application/json',
        }
        return rest_api

    def _submit(self, job):
        jobs_url = urljoin(self._server.url, 'jobs/')
        job_data = {
            'definition': yaml.dump(yaml.load(job, Loader=yaml.CLoader)),
        }
        resp = self._server.session.post(
            jobs_url, json=job_data, allow_redirects=False
        )
        resp.raise_for_status()
        return resp.json()['job_ids'][0]


def get_runtime(runtime_config, **kwargs):
    """Get a LAVA runtime object"""
    return LAVA(runtime_config, **kwargs)
