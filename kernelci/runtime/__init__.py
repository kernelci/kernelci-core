# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2021-2025 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

"""KernelCI Runtime environment base class definition"""

import abc
import importlib
import json
import os
import requests
import yaml

from jinja2 import Environment, FileSystemLoader, ChoiceLoader

from kernelci.config.base import get_system_arch


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

    # pylint: disable=unused-argument,too-many-arguments
    def __init__(self, config, *, user=None, token=None,
                 custom_template_dir=None, kcictx=None):
        """A Runtime object can be used to run jobs in a runtime environment

        *config* is a kernelci.config.runtime.Runtime object
        *custom_template_dir* is an optional custom directory for Jinja2 templates
        *kcictx* is an optional KernelCI context object for passing program context
        """
        self._config = config
        self._templates = self.TEMPLATES.copy()
        if custom_template_dir:
            # Add the main custom dir
            self._templates.append(custom_template_dir)
            # Add relevant subdirectories
            for subdir in ["runtime", "runtime/base", "runtime/boot", "runtime/tests"]:
                sub_path = (
                    os.path.join(custom_template_dir, subdir)
                    if not custom_template_dir.endswith(subdir)
                    else custom_template_dir
                )
                if os.path.isdir(sub_path):
                    self._templates.append(sub_path)
        self._user = user
        self._token = token
        self._stored_url = None

    @property
    def config(self):
        """RuntimeConfig object for this Runtime instance"""
        return self._config

    @property
    def templates(self):
        """List of template directories used with this runtime"""
        return self._templates

    def _get_template(self, job_config):
        loaders = [FileSystemLoader(path) for path in self.templates]
        jinja2_env = Environment(
            loader=ChoiceLoader(loaders),
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

    def _get_storage_config(self, kcictx, storage_name=None):
        """Get storage configuration and initialize storage

        *kcictx* is the KernelCI context object
        *storage_name* is an optional storage name to use

        Returns a tuple of (storage object, storage_name)
        """
        if not kcictx:
            raise ValueError(
                "Context is required for external storage but was not provided"
            )

        # Get storage configuration name
        if not storage_name:
            # Get default storage configuration name from TOML [DEFAULT] section
            storage_name = kcictx.get_default_storage_config()

        if not storage_name:
            # Fallback to first available storage if no default is specified
            storage_names = kcictx.get_storage_names()
            if not storage_names:
                raise ValueError("No storage configurations found in context")
            storage_name = storage_names[0]

        storage = kcictx.init_storage(storage_name)
        if not storage:
            raise ValueError(f"Failed to initialize storage '{storage_name}'")

        return storage, storage_name

    def get_job_definition_url(self):
        """Get the URL where the job definition was stored if any"""
        return self._stored_url

    def get_params(self, job, api_config=None):
        """Get job template parameters"""
        instanceid = os.environ.get('KCI_INSTANCE')
        instance_callback = os.environ.get('KCI_INSTANCE_CALLBACK')
        device_dtb = None
        device_type = job.platform_config.name
        if job.platform_config.base_name and len(job.platform_config.base_name) > 0:
            device_type = job.platform_config.base_name
        if job.platform_config.dtb and len(job.platform_config.dtb) > 0:
            # verify if we have metadata at all
            if 'metadata' not in job.node['artifacts']:
                raise ValueError(
                    f"metadata.json not found for dtb file "
                    f"{job.platform_config.dtb}"
                )
            # Fetch metadata.json and add platform dtb to artifacts list
            metadata_url = job.node['artifacts']['metadata']
            req = requests.get(metadata_url, timeout=60)
            if req.status_code != 200:
                raise ValueError(
                    f"Failed to fetch metadata.json from "
                    f"{metadata_url}: HTTP {req.status_code}"
                )
            metadata = req.json()
            for dtb in job.platform_config.dtb:
                if dtb in metadata['artifacts']:
                    dtb_url = metadata['artifacts'][dtb]
                    job.node['artifacts']['dtb'] = dtb_url
                    device_dtb = dtb
                    break
            if not device_dtb:
                raise ValueError(
                    f"dtb file {job.platform_config.dtb} not found!"
                )

        params = {
            'api_config': api_config or {},
            'storage_config': job.storage_config or {},
            'platform_config': job.platform_config or {},
            'instanceid': instanceid,
            'instance_callback': instance_callback,
            'name': job.name,
            'node': job.node,
            'runtime': self.config.lab_type,
            'runtime_image': job.config.image,
            'device_type': device_type,
        }
        if job.platform_config.params:
            params.update(job.platform_config.params)
        if device_dtb:
            params['device_dtb'] = device_dtb
        params.update(job.config.params)
        arch = params.get('arch') or job.platform_config.arch
        for system in ('brarch', 'crosarch', 'debarch', 'karch'):
            params.update({system: get_system_arch(system, arch)})
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


def get_runtime(config, user=None, token=None, custom_template_dir=None, kcictx=None):
    """Get the Runtime object for a given runtime config.

    *config* is a kernelci.config.runtime.Runtime object
    *user* is the name of the user to connect to the runtime
    *token* is the associated token to connect to the runtime
    *custom_template_dir* is an optional custom directory for Jinja2 templates
    *kcictx* is an optional KernelCI context object for passing program context
    """
    module_name = '.'.join(['kernelci', 'runtime', config.lab_type])
    runtime_module = importlib.import_module(module_name)
    return runtime_module.get_runtime(config, user=user, token=token,
                                      custom_template_dir=custom_template_dir,
                                      kcictx=kcictx)


def get_all_runtimes(runtime_configs, opts, custom_template_dir=None, kcictx=None):
    """Get all the Runtime objects based on the runtime configs and options

    This will iterate over all the runtimes configs and yield a (name, runtime)
    2-tuple for each Runtime object being constructed.  The options are used to
    find the user name and token for each runtime, if applicable.

    *runtime_configs* is the 'runtimes' config loaded from YAML
    *opts* is an Options object loaded from the CLI args and settings file
    *custom_template_dir* is an optional custom directory for Jinja2 templates
    *kcictx* is an optional KernelCI context object for passing program context
    """
    for config_name, config in runtime_configs.items():
        section = ('runtime', config_name)
        user, token = (
            opts.get_from_section(section, opt)
            for opt in ('user', 'runtime_token')
        )
        runtime = get_runtime(config, user=user, token=token,
                              custom_template_dir=custom_template_dir,
                              kcictx=kcictx)
        yield config_name, runtime


def evaluate_test_suite_result(child_nodes):
    """ Evaluate test suite result
    Argument: List of child nodes with the below format:
    [
        {
            "node": {
                "name": <node-name>,
                "result":<node-result>
            },
            "child_nodes": []
        },
        ...
    ]

    If all child nodes pass, the suite will be marked 'pass'
    If one of the child node fails, the suite will be marked `fail`
    If all child nodes skipped, the suite will be marked 'skip'
    If atleast one of the child passes and other are skipped, the suite
    will be marked as `pass`
    If atleast one of the child skipped and other are unknown, the
    suite will be marked as `skip`
    """
    result = None
    result_list = [child['node']['result'] for child in child_nodes]
    if 'fail' in result_list:
        result = 'fail'
    elif all(result == 'pass' for result in result_list) or 'pass' in result_list:
        result = 'pass'
    elif all(result == 'skip' for result in result_list) or 'skip' in result_list:
        result = 'skip'
    return result
