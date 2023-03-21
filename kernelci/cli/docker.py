# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Tool to generate Dockerfiles from Jinja2 templates and build images"""


import io
import json

from jinja2 import Environment, FileSystemLoader
import docker

from .base import Command, sub_main


class DockerCommand(Command):
    """Base command class for docker sub-commands"""

    args = Command.args + [
        {
            'name': 'image',
            'help': "Docker image name, e.g. gcc-10:x86",
        },
        {
            'name': '--prefix',
            'help': "Docker image tag prefix",
        },
    ]
    opt_args = Command.opt_args + [
        {
            'name': '--arch',
            'help': "CPU architecture, e.g. x86",
        },
        {
            'name': 'fragments',
            'nargs': '*',
            'help': "Extra fragments, e.g. kernelci",
        },
        {
            'name': '--image-version',
            'help': "Docker image version tag e.g. 20221011.0",
        },
    ]

    @classmethod
    def _gen_image_name(cls, args):
        base_name = args.prefix + args.image
        tag_strings = [args.arch] if args.arch else []
        if args.fragments:
            tag_strings.extend(args.fragments)
        if args.image_version:
            tag_strings.append(args.image_version)
        tag_name = '-'.join(tag_strings)
        name = ':'.join((base_name, tag_name)) if tag_name else base_name
        return base_name, tag_name, name


class DockerBuildGenerateCommand(DockerCommand):
    """Base command class for docker generate and build sub-commands"""

    TEMPLATE_PATHS = [
        'config/docker',
        '/etc/kernelci/config/docker',
    ]

    @classmethod
    def _get_template_params(cls, prefix, fragments):
        params = {
                'prefix': prefix,
                'fragments': [
                    f'fragment/{fragment}.jinja2'
                    for fragment in fragments
                ] if fragments else []
            }
        return params

    def _gen_dockerfile(self, img_name, params):
        jinja2_env = Environment(loader=FileSystemLoader(self.TEMPLATE_PATHS))
        template = jinja2_env.get_template(f"{img_name}.jinja2")
        return template.render(params)

    def _get_dockerfile(self, args):
        params = self._get_template_params(args.prefix, args.fragments)
        template = (
            '-'.join((args.image, args.arch)) if args.arch else args.image
        )
        return self._gen_dockerfile(template, params)


class cmd_build(DockerBuildGenerateCommand):  # pylint: disable=invalid-name
    """Build image"""

    opt_args = DockerCommand.opt_args + [
        {
            'name': '--build-arg',
            'action': 'append',
            'help': "Build argument to pass to docker build",
        },
        {
            'name': '--no-cache',
            'action': 'store_true',
            'help': "Disable Docker cache when building the image",
        },
        {
            'name': '--push',
            'action': 'store_true',
            'help': "Push the image to Docker Hub after building",
        },
        {
            'name': '--verbose',
            'action': 'store_true',
            'help': "Verbose output",
        },
    ]

    @classmethod
    def _build_image(cls, dockerfile, tag, buildargs, nocache):
        client = docker.from_env()
        dockerfile_obj = io.BytesIO(dockerfile.encode())
        return client.images.build(
            fileobj=dockerfile_obj, tag=tag, buildargs=buildargs,
            nocache=nocache,
        )

    @classmethod
    def _dump_dockerfile(cls, dockerfile):
        sep = '--------------------------------------------------' * 2
        print()
        print(sep)
        print(dockerfile)
        print(sep)
        print()

    @classmethod
    def _dump_log(cls, build_log):
        for chunk in build_log:
            stream = chunk.get('stream') or ""
            for line in stream.splitlines():
                print(line)

    @classmethod
    def _push_image(cls, base_name, tag_name):
        client = docker.from_env()
        push_log_json = client.images.push(base_name, tag_name)
        return list(
            json.loads(json_line)
            for json_line in push_log_json.splitlines()
        )

    @classmethod
    def _dump_push_log(cls, log):
        for line in log:
            if 'status' in line and 'progressDetail' not in line:
                print(line['status'])

    def __call__(self, configs, args):
        base_name, tag_name, name = self._gen_image_name(args)

        dockerfile = self._get_dockerfile(args)
        if args.verbose:
            self._dump_dockerfile(dockerfile)

        print(f"Building {name}")
        buildargs = dict(
            barg.split('=') for barg in args.build_arg
        ) if args.build_arg else {}
        _, build_log = self._build_image(
            dockerfile, name, buildargs, args.no_cache
        )
        if args.verbose:
            self._dump_log(build_log)
        if args.push:
            print(f"Pushing {name} to Docker Hub")
            push_log = self._push_image(base_name, tag_name)
            if args.verbose:
                self._dump_push_log(push_log)
            for line in push_log:
                error = line.get('errorDetail')
                if error:
                    print(error['message'])
                    return False
        return True


class cmd_generate(DockerBuildGenerateCommand):  # pylint: disable=invalid-name
    """Generate Dockerfile from Jinja2 template"""

    def __call__(self, configs, args):
        print(self._get_dockerfile(args))
        return True


class cmd_name(DockerCommand):  # pylint: disable=invalid-name
    """Get the full name of a Docker image without building it"""

    def __call__(self, configs, args):
        _, _, name = self._gen_image_name(args)
        print(name)
        return True


def main(args=None):
    """Entry point for the command line tool"""
    sub_main("docker", globals(), args)
