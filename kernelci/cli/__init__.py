#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI command line utilities

This module provides base features for KernelCI command line tools.  Based on
the Click framework, it adds support for loading default values and secrets
from TOML settings.
"""

import email.policy
import functools
import json
import re
import typing

import click
import requests

import kernelci.api
import kernelci.api.helper
import kernelci.config
import kernelci.settings


class Args:  # pylint: disable=too-few-public-methods
    """Common command line arguments"""
    api = click.option(
        '--api',
        help="Name of the API config entry"
    )
    config = click.option(
        '-c', '--yaml-config', 'config', multiple=True,
        help="Path to the YAML pipeline configuration"
    )
    indent = click.option(
        '--indent', type=int,
        help="Intentation level for structured data output"
    )
    page_length = click.option(
        '-l', '--page-length', type=int,
        help="Page length in paginated data"
    )
    page_number = click.option(
        '-n', '--page-number', type=int,
        help="Page number in paginated data"
    )
    runtime = click.option(
        '--runtime',
        help="Name of the runtime config entry"
    )
    settings = click.option(
        '-s', '--toml-settings', 'settings',
        help="Path to the TOML user settings"
    )
    storage = click.option(
        '--storage',
        help="Name of the storage config entry"
    )
    verbose = click.option(
        '-v', '--verbose/--no-verbose', default=None,
        help="Print more details output"
    )


def catch_error(func):
    """Decorator to catch HTTPError and KeyError exceptions and raise
    a ClickException"""
    @functools.wraps(func)
    def call(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as ex:
            raw_content_type = ex.response.headers.get('content-type')
            header = email.policy.EmailPolicy.header_factory(
                'content-type', raw_content_type
            )
            detail = (
                ex.response.json().get('detail')
                if header.content_type == 'application/json'
                else None
            )
            raise click.ClickException(
                '\n'.join((str(ex), detail)) if detail else ex
            ) from ex
        except KeyError as ex:
            raise click.ClickException(
                f"KerError: Value not found for {str(ex)}") from ex
    return call


class CommandSettings:
    """Settings object passed to commands via the context"""

    def __init__(self, settings_path):
        self._settings = kernelci.settings.Settings(settings_path)

    def __getattr__(self, *args):
        """Get a settings value for the current command group"""
        return self.get(*args)

    @property
    def settings(self):
        """TOML Settings object"""
        return self._settings

    def get(self, *args):
        """Get a settings value like __getattr__()"""
        return self._settings.get(*args)

    def get_secrets(self, params, root):
        """Get a Secrets object with the secrets loaded from the settings"""
        return kernelci.settings.Secrets(self._settings, params, root)


class Kci(click.Command):
    """Wrapper command to load settings and populate default values"""

    def __init__(self, *args, kci_secrets: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self._kci_secrets = kci_secrets

    def _walk_name(self, ctx):
        name = (ctx.info_name,)
        if ctx.parent:
            return self._walk_name(ctx.parent) + name
        return name

    def invoke(self, ctx):
        path = self._walk_name(ctx)
        params = {}
        settings = ctx.obj
        for key, value in ctx.params.items():
            if isinstance(value, (tuple, set)):
                value = list(value)
            if value is None or value == []:
                value = settings.get(*path, key)
            params[key] = value
        if self._kci_secrets:
            root = (path[0], 'secrets')
            params['secrets'] = settings.get_secrets(params, root)
        ctx.params = params
        super().invoke(ctx)


class KciS(Kci):
    """Wrapper command with `secrets` as additional function argument"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, kci_secrets=True, **kwargs)


# pylint: disable=not-callable
class KciGroup(click.core.Group):
    """Click group to create commands with Kci or KciS classes"""

    def command(self, *args, cls=Kci, secrets=False, **kwargs):
        """Wrapper for the command decorator to use Kci or KciS

        If secrets is set to True, the class used for the command is always
        KciS.  Otherwise, Kci is used by default.
        """
        kwargs['cls'] = KciS if secrets is True else cls
        decorator = super().command(**kwargs)
        return decorator if not args else decorator(args[0])

    def group(self, *args, cls=None, **kwargs):
        """Wrapper to use KciGroup for sub-groups"""
        kwargs['cls'] = cls or self.__class__
        decorator = super().group(**kwargs)
        return decorator if not args else decorator(args[0])


@click.group(cls=KciGroup)
@Args.settings
@click.pass_context
def kci(ctx, settings):
    """Entry point for the kci command line tool"""
    ctx.obj = CommandSettings(settings)


def split_attributes(attributes: typing.List[str]):
    """Split attributes into a dictionary.

    Split the attribute strings into a dictionary using `=` as a delimiter
    between the key and the value e.g. key=value.  The API operators are
    expected to be part of the key, for example score__gte=100 to find objects
    with a 'score' attribute with a value greater or equal to 100.

    As a syntactic convenience, if the operator matches one of >, <, >=, <=, !=
    then the corresponding API operator '__gt', '__lt', '__gte', '__lte',
    '__ne' is added to the key name automatically.  Spaces can also be used
    around the operators, although this typically means adding double quotes on
    the command line around each attribute.  As such, the example used
    previously is equivalent to "score >= 100".
    """
    operators = {
        '>': '__gt',
        '<': '__lt',
        '>=': '__gte',
        '<=': '__lte',
        '!=': '__ne',
        '=': '',
    }
    pattern = re.compile(r'^([.a-zA-Z0-9_-]+) *([<>!=]+) *(.*)')

    attributes = attributes or []
    parsed = {}
    for attribute in attributes:
        match = pattern.match(attribute)
        if not match:
            raise click.ClickException(f"Invalid attribute: {attribute}")
        name, operator, value = match.groups()
        opstr = operators.get(operator)
        if opstr is None:
            raise click.ClickException(f"Invalid operator: {operator}")
        parsed.setdefault(''.join((name, opstr)), []).append(value)

    return {
        name: value[0] if len(value) == 1 else value
        for name, value in parsed.items()
    }


def get_pagination(page_length: int, page_number: int):
    """Get the offset and limit values for paginated data

    Return a 2-tuple (offset, limit) which can be used with paginated data from
    the API.  The `page_length` and `page_number` values are used to get the
    absolute start `offset`.  The `page_length` value is the same as the
    `limit` API value, essentially the maximum number of items per page.
    """
    if page_length is None:
        page_length = 10
    elif page_length < 1:
        raise click.UsageError(
            f"Page length must be at least 1, got {page_length}"
        )
    if page_number is None:
        page_number = 0
    elif page_number < 0:
        raise click.UsageError(
            f"Page number must be at least 0, got {page_number}"
        )
    return page_number * page_length, page_length


def get_api(config, api,
            secrets: typing.Optional[kernelci.settings.Secrets] = None):
    """Get an API object instance

    Return an API object based on the given `api` config name loaded from the
    YAML config found in the `config` path or in the `config` dictionary
    already loaded.
    """
    if not isinstance(config, dict):
        config = kernelci.config.load(config)
    api_config = config['api'][api]
    token = secrets.api.token if secrets else None
    return kernelci.api.get_api(api_config, token)


def get_api_helper(*args, **kwargs):
    """Wrapper around get_api() to get an APIHelper object"""
    api = get_api(*args, **kwargs)
    return kernelci.api.helper.APIHelper(api)


def echo_json(data, indent):
    """Dump the JSON data with the provided indent on stdout

    This is a convenience function for a very common use-case where some JSON
    data received from the API needs to be dumped on stdout.  If indent is 0
    then no identation is applied rather than indentation with 0 spaces (line
    returns).
    """
    click.echo(json.dumps(data, indent=indent or None))
