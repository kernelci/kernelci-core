# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""Common definitions for commands that interact with the API

In order to avoid adding a dependency on all the commands to the kernelci.api
module, the common code for commands that need to interact with the API is
provided here separately instead.
"""

import abc
import json
import re

import kernelci.api
from .base import Command, Args, catch_http_error


class APICommand(Command):  # pylint: disable=too-few-public-methods
    """Base command class for interacting with the KernelCI API

    The Args.api_token argument needs to be added for commands that require
    authentication with the API.
    """
    args = Command.args + [Args.api_config]

    @classmethod
    def _get_api(cls, configs, args):
        config = configs['api'][args.api_config]
        return kernelci.api.get_api(config, args.api_token)

    @classmethod
    def _print_json(cls, data, indent=None):
        n_indent = None if indent is None else int(indent)
        print(json.dumps(data, indent=n_indent))

    @classmethod
    def _load_json(cls, json_path, encoding='utf-8'):
        with open(json_path, encoding=encoding) as json_file:
            return json.load(json_file)

    @classmethod
    def _print_node(cls, node, id_only, indent):
        if id_only:
            print(node['id'])
        else:
            cls._print_json(node, indent)

    @abc.abstractmethod
    def _api_call(self, api, configs, args):
        """Entry point to implement commands that use the API"""

    @catch_http_error
    def __call__(self, configs, args):
        api = self._get_api(configs, args)
        return self._api_call(api, configs, args)


class AttributesCommand(APICommand):
    """Base command class for API queries with arbitrary attributes"""
    opt_args = APICommand.opt_args + [
        {
            'name': 'attributes',
            'nargs': '*',
            'help': "Attributes in 'name=value' format, where = is "
            "OPERATOR and can be one of: >, <, >=, <=, =",
        },
    ]

    @classmethod
    def _split_attributes(cls, attributes):
        """ Split attributes into a dictionary.

        At moment we use small hack, if operator matches one of: >, <, >=, <=
        then we append to attribute '__gt', '__lt', '__gte', '__lte', '__ne'
        suffix accordingly to API documentation.
        """
        ret = {}
        if not attributes:
            return ret
        for attribute in attributes:
            pattern = r'^([\S]+)([!=<>]+)([\S]+)$'
            match = re.match(pattern, attribute)
            if match:
                attribute, operator, value = match.groups()
                switch = {
                    '>': '__gt',
                    '<': '__lt',
                    '>=': '__gte',
                    '<=': '__lte',
                    '!=': '__ne',
                }
                if operator in switch:
                    attribute += switch[operator]
                elif operator != '=':
                    raise ValueError(f"Invalid operator {operator}")
                if attribute in ret:
                    raise ValueError(f"Attribute {attribute} already exists")
                ret[attribute] = value
            else:
                raise ValueError(f"Invalid attribute {attribute}")

        return ret
