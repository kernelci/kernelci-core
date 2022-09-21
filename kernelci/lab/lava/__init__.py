# Copyright (C) 2019,2021 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@coll
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
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

from jinja2 import Environment, FileSystemLoader
import os
from kernelci.lab import add_kci_raise, LabAPI, GeneratorAPI


class LavaGeneratorAPI(GeneratorAPI):
    DEFAULT_TEMPLATE_PATHS = ['config/lava', '/etc/kernelci/lava']

    def generate(self, params, device_config, plan_config, callback_opts=None,
                 templates_paths=None):
        if templates_paths is None:
            templates_paths = self.DEFAULT_TEMPLATE_PATHS
        short_template_file = plan_config.get_template_path(
            device_config.boot_method)
        base_name = params['base_device_type']

        # Scale the job priority (from 0-100) within the available levels
        # for the lab, or use the lowest by default.
        if 'priority' in plan_config.params:
            priority = plan_config.params['priority']
            if priority > 100:
                priority = 100
        else:
            priority = 20

        prio_range = self.config._priority_max - self.config._priority_min
        priority = int(((priority * prio_range) / 100) +
                       self.config._priority_min)

        params.update({
            'queue_timeout': self.config.queue_timeout,
            'lab_name': self.config.name,
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

    def job_file_name(self, params):
        return '.'.join([params['name'], 'yaml'])

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


class LavaAPI(LabAPI):

    def submit(self, job_path):
        with open(job_path, 'r') as job_file:
            job = job_file.read()
            job_id = self._submit(job)
            return job_id
