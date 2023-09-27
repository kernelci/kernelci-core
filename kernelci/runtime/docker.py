# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Docker runtime implementation"""

import json
import os

import docker

from . import Runtime


class Docker(Runtime):
    """Runtime implementation to run jobs in a local Docker container

    This runtime can be used to locally start a container and run a generated
    job script in it.  An environment file should be provided with the API
    token and any storage credentials, unless the job is meant to be run
    offline.  An extra file in JSON format is generated alongside the script
    with .meta extension to contain some meta-data such as the Docker image
    name to use.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._docker_client = None
        self._env = self._load_env()

    def _load_env(self):
        if self.config.env_file and os.path.isfile(self.config.env_file):
            with open(self.config.env_file, encoding='utf-8') as env:
                env_list = []
                for line in env.readlines():
                    env_line = line.strip()
                    # Skip empty lines and comments
                    if not env_line or env_line.startswith('#'):
                        continue
                    env_list.append(env_line)

                return env_list
        return None

    @classmethod
    def _meta_path(cls, script_file_path):
        return '.'.join((script_file_path, 'meta'))

    @property
    def _client(self):
        if self._docker_client is None:
            self._docker_client = docker.from_env(timeout=self.config.timeout)
        return self._docker_client

    def generate(self, job, params):
        template = self._get_template(job.config)
        return {
            'job': template.render(params),
            'metadata': {
                'runtime': self.config.name,
                'image': job.config.image,
            },
        }

    def save_file(self, job, *args, **kwargs):
        script, meta = (job[key] for key in ('job', 'metadata'))
        script_file_path = super().save_file(script, *args, **kwargs)
        os.chmod(script_file_path, 0o775)
        meta_file_path = self._meta_path(script_file_path)
        with open(meta_file_path, 'w', encoding='utf-8') as meta_file:
            json.dump(meta, meta_file, indent=4)
        return script_file_path

    def submit(self, job_path):
        meta_file_path = self._meta_path(job_path)
        with open(meta_file_path, encoding='utf-8') as meta_file:
            meta = json.load(meta_file)
        image = meta['image']
        print(f"Pulling image {image}")
        self._client.images.pull(*image.split(':'))
        print("Starting container")
        return self._client.containers.run(
            meta['image'],
            volumes=self.config.volumes,
            user=self.config.user,
            command=os.path.join('/home/kernelci', job_path),
            environment=self._env,
            detach=True
        )

    def get_job_id(self, job_object):
        return job_object.id

    def wait(self, job_object):
        ret = job_object.wait()
        return ret['StatusCode']


def get_runtime(runtime_config, **kwargs):
    """Get a Docker runtime object"""
    return Docker(runtime_config, **kwargs)
