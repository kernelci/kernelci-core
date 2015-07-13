#!/usr/bin/python

import os
import ConfigParser

class Configuration(object):
    def __init__(self, config_sources=None):
        self.config_sources = config_sources or list()


    def add_config_override(self, config_source):
        self.config_sources.insert(0, config_source)


    def get(self, variable_name):
        for config_source in self.config_sources:
            method_name = 'get_%s' % variable_name
            if hasattr(config_source, method_name):
                variable = getattr(config_source, method_name)()
                if variable:
                    return variable


class EnvConfigParser(object):
    def __init__(self):
        self.username = None
        self.token = None
        self.server = None


    def get_username(self):
        if self.username: return self.username

        self.username = os.environ.get('LAVA_USER', None)


    def get_token(self):
        if self.token: return self.token

        self.token = os.environ.get('LAVA_TOKEN', None)


    def get_server(self):
        if self.server: return self.server

        self.server = os.environ.get('LAVA_SERVER', None)


class FileConfigParser(object):
    def __init__(self, filename=None, section=None):
        self.section = section
        self.filename = filename or os.path.expanduser('~/.lavarc')

        self.config_parser = ConfigParser.ConfigParser()

        self.config_parser.readfp(open(self.filename))

        self.username = None
        self.token = None
        self.server = None


    def get_username(self):
        if self.username: return self.username

        if self.config_parser:
            if self.config_parser.has_option(self.section, 'username'):
                self.username = self.config_parser.get(self.section, 'username')
        return self.username


    def get_token(self):
        if self.token: return self.token

        if self.config_parser:
            if self.config_parser.has_option(self.section, 'token'):
                self.token = self.config_parser.get(self.section, 'token')
        return self.token


    def get_server(self):
        if self.server: return self.server

        if self.config_parser:
            if self.config_parser.has_option(self.section, 'server'):
                self.server = self.config_parser.get(self.section, 'server')
        return self.server


class ArgumentParser(object):
    def __init__(self, args):
        self.username = args.get('username')
        self.token = args.get('token')
        self.server = args.get('server')
        self.job = args.get('job')


    def get_username(self):
        return self.username


    def get_token(self):
        return self.token


    def get_server(self):
        return self.server


    def get_job(self):
        return self.job


# vim: set ts=8 sw=4 sts=4 et tw=80 fileencoding=utf-8 :
