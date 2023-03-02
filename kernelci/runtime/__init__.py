# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

import importlib
import json
import os
import yaml


def add_kci_raise(env):
    def template_exception(msg):
        raise Exception(msg)
    env.globals['kci_raise'] = template_exception


class Runtime:
    """Runtime environment"""

    def __init__(self, config, **kwargs):
        """A Runtime object can be used to run jobs in a runtime environment

        *config* is a kernelci.config.runtime.Runtime object
        """
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

    def import_devices(self, data):
        """Import devices information

        Import an arbitrary data structure describing the devices available in
        the runtime environment.

        *data* is the devices data structure to import
        """
        self._devices = data

    def device_type_online(self, device_type_config):
        """Check whether a given device type is online

        Return True if the device type is online in the lab, False otherwise.

        *device_type_config* is a config.test.DeviceType object
        """
        return True

    def job_file_name(self, params):
        """Get the file name where to store the generated job definition."""
        return params['name']

    def match(self, filter_data):
        """Apply filters and return True if they match, False otherwise."""
        return self.config.match(filter_data)

    def get_params(self, node, plan_config, platform_config, api_config=None):
        """Get job template parameters"""
        params = {
            'api_config_yaml': yaml.dump(api_config),
            'name': plan_config.name,
            'node_id': node['_id'],
            'revision': node['revision'],
            'runtime': self.config.lab_type,
            'runtime_image': plan_config.image,
            'tarball_url': node['artifacts']['tarball'],
        }
        params.update(plan_config.params)
        params.update(platform_config.params)
        return params

    def generate(self, params, device_config, plan_config, callback_opts=None,
                 templates_paths=None, runtime_config=None):
        """Generate a test job definition.

        *params* is a dictionary with the test parameters which can be used
             when generating a job definition using templates

        *device_config* is a DeviceType configuration object for the target
             device type

        *plan_config* is a TestPlan configuration object for the target test
             plan

        *callback_opts* is a dictionary with extra options used for callbacks

        *templates_paths* is an optional argument to specify the path(s) where
            the template files should be found, when not in the standard
            location.  This could be either a string or a list of strings to
            provide several paths.

        *runtime_config* is a configuration object for the runtime environment
        """
        raise NotImplementedError("Runtime.generate() is required")

    def save_file(self, job, output_path, params):
        """Save a test job definition in a file.

        *job* is the job definition data
        *output_path* is the directory where the file should be saved
        *params* is a dictionary with template parameters

        Return the full path where the job definition file was saved.
        """
        file_name = self.job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        with open(output_file, 'w') as output:
            output.write(job)
        return output_file

    def submit(self, job_path):
        """Submit a test job definition in a runtime."""
        raise NotImplementedError("Runtime.submit() is required")


def get_runtime(config, user=None, token=None, runtime_json=None):
    """Get the Runtime object for a given runtime config.

    *config* is a kernelci.config.runtime.Runtime object
    *user* is the name of the user to connect to the runtime
    *token* is the associated token to connect to the runtime
    *runtime_json* is the path to a JSON file with cached runtime information
    """
    module_name = '.'.join(['kernelci', 'runtime', config.lab_type])
    runtime_module = importlib.import_module(module_name)
    runtime = runtime_module.get_runtime(config, user=user, token=token)
    if runtime_json:
        with open(runtime_json) as json_file:
            devices = json.load(json_file)['devices']
            runtime.import_devices(devices)
    return runtime
