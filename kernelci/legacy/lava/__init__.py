# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Michal Galka <michal.galka@collabora.com>

from jinja2 import Environment, FileSystemLoader
import json
import os
import re
import sys

CROS_CONFIG_RE = re.compile(r'cros://chromeos-([0-9.]+)/([a-z0-9_]+)/([a-z0-9-._]+).flavour.config(\+[a-z0-9-+]+)?')  # noqa

CROS_FLAVOURS = {
    'chromeos-amd-stoneyridge': 'ston',
    'chromeos-intel-denverton': 'denv',
    'chromeos-intel-pineview': 'pine',
    'chromiumos-arm': 'arm',
    'chromiumos-arm64': 'arm64',
    'chromiumos-mediatek': 'mtk',
    'chromiumos-qualcomm': 'qcom',
    'chromiumos-rockchip': 'rk32',
    'chromiumos-rockchip64': 'rk64',
    'chromiumos-x86_64': 'x86',
}

CROS_DEVICE_TYPES = {
    'hp-x360-12b-ca0500na-n4000-octopus_chromeos': 'octopus-n4000',
    'hp-x360-12b-ca0010nr-n4020-octopus_chromeos': 'octopus-n4020',
    'qemu_x86_64-uefi-chromeos': 'qemu-x86',
}


def add_kci_raise(jinja2_env):
    """Add a kci_raise function to use in templates

    This adds a `kci_raise` function to a given Jinja2 environment `jinja2_env`
    so it can be used to raise exceptions from template files when for example
    some template parameters are not valid.
    """
    def template_exception(msg):
        raise Exception(msg)
    jinja2_env.globals['kci_raise'] = template_exception


class LavaRuntime:
    DEFAULT_TEMPLATE_PATHS = ['config/lava', '/etc/kernelci/lava']

    def __init__(self, config, **kwargs):
        self._config = config
        self._server = self._connect(**kwargs)
        self._devices = None

    @property
    def config(self):
        return self._config

    @property
    def devices(self):
        if self._devices is None:
            self._devices = self._get_devices()
        return self._devices

    def _get_devices(self):
        return list()

    def _connect(self, *args, **kwargs):
        return None

    def import_devices(self, runtime_json):
        with open(runtime_json, encoding='utf-8') as json_file:
            self._devices = json.load(json_file)['devices']

    def device_type_online(self, device_type_config):
        return True

    def job_file_name(self, params):
        return '.'.join([params['name'], 'yaml'])

    def match(self, filter_data):
        return self.config.match(filter_data)

    def generate(self, params, device_config, plan_config, callback_opts=None,
                 templates_paths=None):
        if templates_paths is None:
            templates_paths = self.DEFAULT_TEMPLATE_PATHS
        short_template_file = plan_config.get_template_path(
            device_config.boot_method)
        base_name = params['base_device_type']
        priority = self._get_priority(plan_config)
        params.update({
            'queue_timeout': self.config.queue_timeout,
            'lab_name': self.config.name,
            'base_device_type': self._alias_device_type(base_name),
            'priority': priority,
            'name': self._shorten_cros_name(params),
        })
        if callback_opts:
            self._add_callback_params(params, callback_opts)
        jinja2_env = Environment(loader=FileSystemLoader(templates_paths),
                                 extensions=["jinja2.ext.do"])
        add_kci_raise(jinja2_env)
        template = jinja2_env.get_template(short_template_file)
        data = template.render(params)
        return data

    def save_file(self, job, output_path, params):
        file_name = self.job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        if os.path.isfile(output_file):
            # print error message to stderr
            print("ERROR: file already exists: %s" % output_file,
                  file=sys.stderr)
            return None
        with open(output_file, 'w') as output:
            output.write(job)
        return output_file

    def submit(self, job_path):
        with open(job_path, 'r') as job_file:
            job = job_file.read()
            job_id = self._submit(job)
            return job_id

    def _shorten_cros_defconfig(self, defconfig):
        kver, arch, flav, frag = CROS_CONFIG_RE.match(defconfig).groups()
        frag = frag.strip('+').replace('+', '-') if frag else ''
        flav = CROS_FLAVOURS.get(flav) or flav
        return '-'.join((arch, flav, kver, frag))

    def _shorten_cros_device_type(self, device_type):
        return CROS_DEVICE_TYPES.get(device_type) or device_type

    def _shorten_cros_name(self, params):
        defconfig_full = params['defconfig_full']
        if defconfig_full.startswith('cros:'):
            return '-'.join((
                params['tree'],
                params['git_branch'],
                params['git_describe'],
                params['arch'],
                self._shorten_cros_defconfig(defconfig_full),
                params['build_environment'],
                self._shorten_cros_device_type(params['device_type']),
                params['plan'],
            )).replace('/', '-')
        else:
            return params['name']

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
