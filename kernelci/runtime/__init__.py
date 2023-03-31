# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI Runtime environment base class definition"""

import abc
import importlib
import json
import os
import yaml

from jinja2 import Environment, FileSystemLoader


def add_kci_raise(jinja2_env):
    """Add a kci_raise function to use in templates

    This adds a `kci_raise` function to a given Jinja2 environment `jinja2_env`
    so it can be used to raise exceptions from template files when for example
    some template parameters are not valid.
    """
    def template_exception(msg):
        raise Exception(msg)
    jinja2_env.globals['kci_raise'] = template_exception


class Runtime(abc.ABC):
    """Runtime environment"""

    TEMPLATES = ['config/runtime', '/etc/kernelci/runtime']

    # pylint: disable=unused-argument
    def __init__(self, config, user=None, token=None):
        """A Runtime object can be used to run jobs in a runtime environment

        *config* is a kernelci.config.runtime.Runtime object
        """
        self._config = config
        self._devices = None
        self._templates = self.TEMPLATES

    @property
    def config(self):
        """RuntimeConfig object for this Runtime instance"""
        return self._config

    @property
    def devices(self):
        """List of devices available in this runtime"""
        if self._devices is None:
            self._devices = self._get_devices()
        return self._devices

    @property
    def templates(self):
        """List of template directories used with this runtime"""
        return self._templates

    def _get_devices(self):  # pylint: disable=no-self-use
        return []

    def _get_template(self, job_config):
        jinja2_env = Environment(loader=FileSystemLoader(self.templates))
        return jinja2_env.get_template(job_config.template)

    def import_devices(self, data):
        """Import devices information

        Import an arbitrary data structure describing the devices available in
        the runtime environment.

        *data* is the devices data structure to import
        """
        self._devices = data

    # pylint: disable=unused-argument disable=no-self-use
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

    # This could be refactored with a Job object containing all the config data
    # pylint: disable=too-many-arguments
    def get_params(self, node, job_config, platform_config,
                   api_config=None, storage_config=None):
        """Get job template parameters"""
        params = {
            'api_config_yaml': yaml.dump(api_config or {}),
            'storage_config_yaml': yaml.dump(storage_config or {}),
            'name': job_config.name,
            'node_id': node['_id'],
            'revision': node['revision'],
            'runtime': self.config.lab_type,
            'runtime_image': job_config.image,
            'tarball_url': node['artifacts']['tarball'],
        }
        params.update(job_config.params)
        params.update(platform_config.params)
        return params

    @abc.abstractmethod
    def generate(self, params, job_config):
        """Generate a test job definition.

        *params* is a dictionary with the test parameters which can be used
             when generating a job definition using templates

        *job_config* is a Job configuration object for the target job
        """

    def save_file(self, job, output_path, params, encoding='utf-8'):
        """Save a test job definition in a file.

        *job* is the job definition data
        *output_path* is the directory where the file should be saved
        *params* is a dictionary with template parameters

        Return the full path where the job definition file was saved.
        """
        file_name = self.job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        with open(output_file, 'w', encoding=encoding) as output:
            output.write(job)
        return output_file

    @abc.abstractmethod
    def submit(self, job_path):
        """Submit a test job definition to run."""

    @abc.abstractmethod
    def get_job_id(self, job_object):
        """Get an id for a given job object as returned by submit()."""


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
        with open(runtime_json, encoding='utf-8') as json_file:
            devices = json.load(json_file)['devices']
            runtime.import_devices(devices)
    return runtime
