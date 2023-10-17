# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Generate Dockerfiles from Jinja2 templates and build images"""

import io
import json

import docker
from jinja2 import Environment, FileSystemLoader


class Docker:
    """Helper class to manage KernelCI Docker images"""

    TEMPLATE_PATHS = [
        'config/docker',
        '/etc/kernelci/config/docker',
    ]

    def __init__(self, image, fragments, arch, prefix, version):
        self._image = image
        self._fragments = fragments or []
        self._arch = arch or ''
        self._prefix = prefix or ''
        self._version = version or ''

    @classmethod
    def iterate_build_log(cls, build_log):
        """Iterate all the lines in a Docker build log"""
        for chunk in build_log:
            stream = chunk.get('stream') or ""
            for line in stream.splitlines():
                yield line

    @classmethod
    def iterate_push_log(cls, push_log):
        """Iterate all the status lines in a Docker push log"""
        for line in push_log:
            if 'status' in line and 'progressDetail' not in line:
                yield line['status']

    @classmethod
    def push_image(cls, base_name, tag_name):
        """Push a Docker image to Docker Hub"""
        client = docker.from_env()
        push_log_json = client.images.push(base_name, tag_name)
        return list(
            json.loads(json_line)
            for json_line in push_log_json.splitlines()
        )

    def get_image_name(self):
        """Get the base name, tag name and full image name"""
        base_name = self._prefix + self._image
        tag_strings = [self._arch] if self._arch else []
        if self._fragments:
            tag_strings.extend(self._fragments)
        if self._version:
            tag_strings.append(self._version)
        tag_name = '-'.join(tag_strings)
        name = ':'.join((base_name, tag_name)) if tag_name else base_name
        return base_name, tag_name, name

    def get_dockerfile(self):
        """Get the generated Dockerfile"""
        params = {
            'prefix': self._prefix,
            'fragments': [
                f'fragment/{fragment}.jinja2'
                for fragment in self._fragments
            ] if self._fragments else []
        }
        template_name = (
            '-'.join((self._image, self._arch)) if self._arch else self._image
        )
        jinja2_env = Environment(loader=FileSystemLoader(self.TEMPLATE_PATHS))
        template = jinja2_env.get_template(f"{template_name}.jinja2")
        return template.render(params)

    def build_image(self, name, buildargs, nocache, dockerfile=None):
        """Build the Docker image"""
        if dockerfile is None:
            dockerfile = self.get_dockerfile()
        client = docker.from_env()
        dockerfile_obj = io.BytesIO(dockerfile.encode())
        try:
            _, build_log = client.images.build(
                fileobj=dockerfile_obj, tag=name, buildargs=buildargs,
                nocache=nocache
            )
            build_err = None
        except docker.errors.BuildError as exc:
            build_log = exc.build_log
            build_err = exc.msg
        return build_log, build_err
