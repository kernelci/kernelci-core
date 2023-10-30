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


class Job:
    """Pipeline job"""

    def __init__(self, node, job_config):
        """A Job object can be run using a Runtime environment

        A pipeline Job object can be used with a Runtime to generate a job
        definition and keep track of all the related pieces of data such as the
        configuration from YAML and the API node.

        *node* is the node data for the job from the API
        *job_config* is the Job configuration object loaded from YAML
        """
        self._node = node
        self._config = job_config
        self._platform_config = None  # node['extra']['platform'] ?
        self._storage_config = None  # node['extra']['storage'] ?

    @property
    def node(self):
        """Node data for this job"""
        return self._node

    @property
    def config(self):
        """Configuration for this job loaded from YAML"""
        return self._config

    @property
    def name(self):
        """Name of the job"""
        return self.config.name

    @property
    def platform_config(self):
        """Target platform configuration loaded from YAML"""
        return self._platform_config

    @platform_config.setter
    def platform_config(self, platform_config):
        self._platform_config = platform_config

    @property
    def storage_config(self):
        """Storage configuration loaded from YAML"""
        return self._storage_config

    @storage_config.setter
    def storage_config(self, storage_config):
        self._storage_config = storage_config


class Runtime(abc.ABC):
    """Runtime environment"""

    TEMPLATES = ['config/runtime', '/etc/kernelci/runtime']

    # pylint: disable=unused-argument
    def __init__(self, config, user=None, token=None):
        """A Runtime object can be used to run jobs in a runtime environment

        *config* is a kernelci.config.runtime.Runtime object
        """
        self._config = config
        self._templates = self.TEMPLATES
        self._user = user
        self._token = token

    @property
    def config(self):
        """RuntimeConfig object for this Runtime instance"""
        return self._config

    @property
    def templates(self):
        """List of template directories used with this runtime"""
        return self._templates

    def _get_template(self, job_config):
        jinja2_env = Environment(
            loader=FileSystemLoader(self.templates),
            extensions=["jinja2.ext.do"]
        )
        jinja2_env.globals.update(self._get_jinja2_functions())
        return jinja2_env.get_template(job_config.template)

    @classmethod
    def _get_jinja2_functions(cls):
        """Add custom functions to use in Jinja2 templates"""
        def kci_raise(msg):
            """Raise an exception"""
            raise Exception(msg)  # pylint: disable=broad-exception-raised

        def kci_yaml_dump(data):
            """Dump data to YAML"""
            return yaml.dump(data, indent=2)

        return {
            'kci_raise': kci_raise,
            'kci_yaml_dump': kci_yaml_dump,
        }

    def match(self, filter_data):
        """Apply filters and return True if they match, False otherwise."""
        return self.config.match(filter_data)

    def get_params(self, job, api_config=None):
        """Get job template parameters"""
        params = {
            'api_config': api_config or {},
            'storage_config': job.storage_config or {},
            'platform_config': job.platform_config.to_dict() or {},
            'name': job.name,
            'node': job.node,
            'runtime': self.config.lab_type,
            'runtime_image': job.config.image,
        }
        params.update(job.config.params)
        return params

    @classmethod
    def _get_job_file_name(cls, params):
        """Get the file name where to store the generated job definition."""
        return params['name']

    def save_file(self, job, output_path, params, encoding='utf-8'):
        """Save a test job definition in a file.

        *job* is the job definition data
        *output_path* is the directory where the file should be saved
        *params* is a dictionary with template parameters

        Return the full path where the job definition file was saved.
        """
        file_name = self._get_job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        with open(output_file, 'w', encoding=encoding) as output:
            output.write(job)
        return output_file

    @abc.abstractmethod
    def generate(self, job, params):
        """Generate a test job definition.

        *job* is a Job object for the target job
        *params* is a dictionary with the test parameters which can be used
             when generating a job definition using templates
        """

    @abc.abstractmethod
    def submit(self, job_path):
        """Submit a test job definition to run."""

    @abc.abstractmethod
    def get_job_id(self, job_object):
        """Get an id for a given job object as returned by submit()."""

    @abc.abstractmethod
    def wait(self, job_object):
        """Wait for a job to complete and get the exit status code"""


def get_runtime(config, user=None, token=None):
    """Get the Runtime object for a given runtime config.

    *config* is a kernelci.config.runtime.Runtime object
    *user* is the name of the user to connect to the runtime
    *token* is the associated token to connect to the runtime
    """
    module_name = '.'.join(['kernelci', 'runtime', config.lab_type])
    runtime_module = importlib.import_module(module_name)
    return runtime_module.get_runtime(config, user=user, token=token)


def get_all_runtimes(runtime_configs, opts):
    """Get all the Runtime objects based on the runtime configs and options

    This will iterate over all the runtimes configs and yield a (name, runtime)
    2-tuple for each Runtime object being constructed.  The options are used to
    find the user name and token for each runtime, if applicable.

    *runtime_configs* is the 'runtimes' config loaded from YAML
    *opts* is an Options object loaded from the CLI args and settings file
    """
    for config_name, config in runtime_configs.items():
        section = ('runtime', config_name)
        user, token = (
            opts.get_from_section(section, opt)
            for opt in ('user', 'runtime_token')
        )
        yield config_name, get_runtime(config, user, token)
