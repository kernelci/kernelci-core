# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Tool to build and manage Docker images"""

import functools
import time

import click
import docker

from kernelci.docker import Docker

from . import Args, kci

PUSH_ATTEMPTS = 3
PUSH_RETRY_DELAY = 5


def kci_docker_args(func):
    """Decorator to add common arguments to a `kci docker` command"""

    @click.argument("image")
    @click.argument("fragments", nargs=-1)
    @click.option("--arch", help="CPU architecture, e.g. x86")
    @click.option("--prefix", help="Prefix used in Docker image names and tags")
    @click.option("--version", help="Image version tag, e.g. 20221011.0")
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        return func(*args, **kwargs)

    return new_func


@kci.group(name="docker")
def kci_docker():
    """Build and manage Docker images

    The image and fragment names are positional arguments.  For example:

        kci docker build gcc-12 --arch=x86 kernelci kselftest

        kci docker generate kernelci
    """


@kci_docker.command
@kci_docker_args
def generate(image, fragments, arch, prefix, version):
    """Generate a Dockerfile"""
    helper = Docker(image, fragments, arch, prefix, version)
    click.echo(helper.get_dockerfile())


@kci_docker.command
@kci_docker_args
def name(image, fragments, arch, prefix, version):
    """Get the full name of a Docker image without building it"""
    helper = Docker(image, fragments, arch, prefix, version)
    _, _, image_name = helper.get_image_name()
    click.echo(image_name)


def _get_docker_args(build_arg):
    try:
        docker_args = (
            dict(barg.split("=") for barg in build_arg) if build_arg else {}
        )
        return docker_args
    except ValueError as exc:
        raise click.UsageError(f"Invalid --build-arg value: {exc}")


def _do_push(helper, base_name, tag_name, verbose):
    retry_delay = PUSH_RETRY_DELAY
    for attempt in range(1, PUSH_ATTEMPTS + 1):
        try:
            push_log = helper.push_image(base_name, tag_name)
            if verbose:
                for line in helper.iterate_push_log(push_log):
                    click.echo(line)
            error_message = next(
                (
                    line["errorDetail"]["message"]
                    for line in push_log
                    if line.get("errorDetail")
                ),
                None,
            )
        except docker.errors.DockerException as exc:
            error_message = str(exc)

        if error_message is None:
            return
        if attempt == PUSH_ATTEMPTS:
            raise click.ClickException(error_message)

        click.echo(
            f"Push failed: {error_message}; retrying in {retry_delay} seconds"
        )
        time.sleep(retry_delay)
        retry_delay *= 2


@kci_docker.command
@kci_docker_args
@Args.verbose
@click.option("--build-arg", multiple=True, help="Docker build arguments")
@click.option("--cache/--no-cache", default=True, help="Use docker cache")
@click.option("--push/--no-push", help="Push the image to Docker Hub")
def build(image, fragments, arch, prefix, **kwargs):
    """Build a Docker image"""
    helper = Docker(image, fragments, arch, prefix, kwargs.get("version"))
    base_name, tag_name, img_name = helper.get_image_name()
    click.echo(f"Building {img_name}")
    verbose = kwargs.get("verbose")
    if verbose:
        click.echo(helper.get_dockerfile())
    docker_args = _get_docker_args(kwargs.get("build_arg"))
    nocache = not kwargs.get("cache")
    build_log, build_err = helper.build_image(img_name, docker_args, nocache)
    if verbose:
        for line in helper.iterate_build_log(build_log):
            click.echo(line)
    if build_err:
        raise click.ClickException(build_err)
    if kwargs.get("push"):
        click.echo(f"Pushing {img_name} to Docker Hub")
        _do_push(helper, base_name, tag_name, verbose)
