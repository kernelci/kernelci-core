# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2018-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""Common definitions for KernelCI command line tools

This module contains common utilities for implementing command line tools that
can't be defined in __init__.py as it would create a circular dependency due to
the commands registration mechanism.
"""

import abc
import argparse
import configparser
import os.path
import sys
import toml

from requests.exceptions import HTTPError

import kernelci.config


# -----------------------------------------------------------------------------
# Standard arguments that can be used in sub-commands
#

class Args:  # pylint: disable=too-few-public-methods
    """A list of all the common command line argument options

    All the members of this class are arguments that can be reused in various
    command line tools.  They are dictionaries with at least a `name`
    attribute, and all the other ones are passed as keyword arguments to the
    add_argument() method of the parser object from argparse.  There should
    also always be a `help` attribute, as this is needed by the Command class.
    """
    SECTION_API = ('api', 'api_config')
    SECTION_DB = ('db', 'db_config')
    SECTION_RUNTIME = ('runtime', 'runtime_config')
    SECTION_STORAGE = ('storage', 'storage_config')

    arch = {
        'name': '--arch',
        'help': "CPU architecture name",
    }

    api = {
        'name': '--api',
        'help': "Backend API URL",
        'section': SECTION_DB,
    }

    api_config = {
        'name': '--api-config',
        'help': "KernelCI API configuration",
    }

    api_token = {
        'name': '--api-token',
        'help': "KernelCI API token",
        'section': SECTION_API,
    }

    build_output = {
        'name': '--build-output',
        'help': "Path to the build output directory",
    }

    bmeta_json = {
        'name': '--bmeta-json',
        'help': "Path to the build.json file",
    }

    branch = {
        'name': '--branch',
        'help': "Name of a kernel branch in a tree",
    }

    build_config = {
        'name': '--build-config',
        'help': "Build config name",
    }

    build_env = {
        'name': '--build-env',
        'help': "Build environment name",
    }

    callback_dataset = {
        'name': '--callback-dataset',
        'help': "Dataset to include in a LAVA callback",
        'section': SECTION_DB,
    }

    callback_id = {
        'name': '--callback-id',
        'help': "Callback identifier used to look up an authentication token",
        'section': SECTION_DB,
    }

    callback_type = {
        'name': '--callback-type',
        'help': "Type of callback URL",
        'section': SECTION_DB,
    }

    callback_url = {
        'name': '--callback-url',
        'help': "Base URL for the callback",
        'section': SECTION_DB,
    }

    cc = {
        'name': '--cc',
        'help': "Recipients to be added as Cc:",
    }

    channel = {
        'name': 'channel',
        'help': "Name of the Pub/Sub channel to subscribe to",
    }

    commit = {
        'name': '--commit',
        'help': "Git commit checksum",
    }

    data_file = {
        'name': '--data-file',
        'help': "Path to the file with data to be submitted to storage",
    }

    data_path = {
        'name': '--data-path',
        'help': "Path to the debos files",
    }

    db_config = {
        'name': '--db-config',
        'help': 'Database config name',
    }

    db_token = {
        'name': '--db-token',
        'help': "Database token",
        'section': SECTION_DB,
    }

    defconfig = {
        'name': '--defconfig',
        'help': "Kernel defconfig name",
    }

    delete = {
        'name': '--delete',
        'help': "Delete the tarball after extracting",
        'action': 'store_true'
    }

    describe = {
        'name': '--describe',
        'help': "Git describe",
    }

    describe_verbose = {
        'name': '--describe-verbose',
        'help': "Verbose version of git describe",
    }

    device_id = {
        'name': '--device-id',
        'help': "Limit test job to run on a specific device",
    }

    dtbs_json = {
        'name': '--dtbs-json',
        'help': "Path to the dtbs.json file",
    }

    group_id = {
        'name': 'group_id',
        'help': "User group id",
    }

    id = {
            'name': 'id',
            'help': "Node id",
    }

    id_only = {
        'name': '--id-only',
        'action': 'store_true',
        'help': "Only print the node ID rather than the full node data",
    }

    indent = {
        'name': '--indent',
        'type': int,
        'help': "Number of indentation spaces in JSON output",
    }

    install = {
        'name': '--install',
        'action': 'store_true',
        'help': "Install the build artifacts ",
    }

    install_path = {
        'name': '--install-path',
        'help':
        "Path to the install directory, or _install_ inside kdir by default",
    }

    is_admin = {
        'name': '--is-admin',
        'help': "Create an admin user",
        'action': 'store_true',
    }

    j = {
        'name': '-j',
        'help': "Number of parallel build processes",
    }

    jobs = {
        'name': '--jobs',
        'help': "File pattern with jobs to submit",
    }

    json_path = {
        'name': '--json-path',
        'help': "Path to the JSON file",
    }

    kdir = {
        'name': '--kdir',
        'help': "Path to the kernel checkout directory",
    }

    kernel_tarball = {
        'name': '--kernel-tarball',
        'help': "Kernel source tarball destination filename",
    }

    runtime_config = {
        'name': '--runtime-config',
        'help': 'Runtime environment config name',
    }

    runtime_json = {
        'name': '--runtime-json',
        'help': "Path to a JSON file with runtime-specific info",
        'section': SECTION_RUNTIME,
    }

    runtime_token = {
        'name': '--runtime-token',
        'help': "Runtime environment token or credentials",
        'section': SECTION_RUNTIME,
    }

    log = {
        'name': '--log',
        'help': "Path to log file",
    }

    limit = {
        'name': '--limit',
        'type': int,
        'help': """\
Maximum number of results to retrieve. When set to 0, no limit is used and all
the matching results are retrieved.""",
        'default': 10,
    }

    mach = {
        'name': '--mach',
        'help': "Mach name (aka SoC family)",
    }

    mirror = {
        'name': '--mirror',
        'help': "Path to the local kernel git mirror",
    }

    mod_path = {
        'name': '--mod-path',
        'help':
        "Path to the installed modules, or _modules_ inside output by default",
    }

    output = {
        'name': '--output',
        'help': "Path the output directory",
    }

    offset = {
        'name': '--offset',
        'type': int,
        'help': "Offset for paginated results",
    }

    password = {
        'name': '--password',
        'help': "Password of a new user",
    }

    plan = {
        'name': '--plan',
        'help': "Test plan name",
    }

    publish_path = {
        'name': '--publish-path',
        'help': "Relative path where build artifacts are published",
    }

    retries = {
        'name': '--retries',
        'help': 'Number of retries before download fails',
        'type': int,
    }

    rootfs_config = {
        'name': '--rootfs-config',
        'help': "Root file system config name",
    }

    rootfs_dir = {
        'name': '--rootfs-dir',
        'help': "Path to the rootfs images directory",
    }

    rootfs_type = {
        'name': '--rootfs-type',
        'help': "Rootfs type",
        'type': str,
        'choices': ('debos', 'buildroot', 'chromiumos')
    }

    storage_config = {
        'name': '--storage-config',
        'help': "Storage configuration name",
    }

    storage_cred = {
        'name': '--storage-cred',
        'help': "Credentials to be used with the storage service",
        'section': SECTION_STORAGE,
    }

    sub_id = {
        'name': 'sub_id',
        'help': "Pub/Sub subscription id",
        'type': int,
    }

    target = {
        'name': '--target',
        'help': "Name of a target platform",
    }

    to = {
        'name': '--to',
        'help': "Recipients to be added as To:",
    }

    tree_name = {
        'name': '--tree-name',
        'help': "Name of a kernel tree",
    }

    tree_url = {
        'name': '--tree-url',
        'help': "URL of a kernel tree",
    }

    upload_path = {
        'name': '--upload-path',
        'help': "Destination upload path on storage",
    }

    url = {
        'name': '--url',
        'help': "Kernel sources download URL",
    }

    user = {
        'name': '--user',
        'help': "Runtime environment user name",
        'section': SECTION_RUNTIME,
    }

    username = {
        'name': '--username',
        'help': "Name of a new user",
    }

    variant = {
        'name': '--variant',
        'help': "Build config variant name",
    }

    verbose = {
        'name': '--verbose',
        'help': "Verbose output",
        'action': 'store_true',
    }


def catch_http_error(func):
    """Decorator to catch HTTPError exceptions and print the error"""
    def call(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as ex:
            print(ex, file=sys.stderr)
            detail = ex.response.json().get('detail')
            if detail:
                print(detail, file=sys.stderr)
            return False
    return call


class Command(abc.ABC):
    """A command helper class.

    It contains several class attributes:

    *help* is the help message passed to tbe sub-parser
    *args* is a list of required arguments dictionaries to add to the parser
    *opt_args* is a list of optional arguments to add to the parser
    """

    help = None
    args = []
    opt_args = []

    def __init__(self, sub_parser, name):
        """This class is to facilitate creating command line utilities

        Each command uses a separate sub-parser to be able to have a different
        set of arguments.  A Command object is callable like a function, so it
        is also possible to simply have a function in the command line tool
        instead.

        *sub_parser* is a sub-parser from argparse for this particular command.
        *name* is the name of the command as used on the command line.

        """
        if not self.help:
            self.help = self.__doc__
        self._parser = sub_parser.add_parser(name, help=self.help)
        for arg_list in [self.args, self.opt_args]:
            if arg_list:
                for arg in arg_list:
                    self._add_arg(arg)
        self._parser.set_defaults(func=self)
        self._args_dict = {}
        for arg_list in [self.args, self.opt_args]:
            if arg_list:
                self._args_dict.update({
                    self.to_opt_name(arg['name']): arg
                    for arg in arg_list
                })

    @abc.abstractmethod
    def __call__(self, configs, args):
        """Call the command

        *configs* is a dictionary with configuration objects parsed from YAML
        *args* is the parsed command line arguments
        """

    def _add_arg(self, arg):
        kwargs = arg.copy()
        arg_name = kwargs.pop('name')
        kwargs.pop('section', None)
        self._parser.add_argument(arg_name, **kwargs)

    def get_arg_data(self, arg_name):
        """Get the data associated with an argument definition

        Get the dictionary with the data associated with an argument using the
        option form of the name.  For example, to get the data associated with
        `--db-token` argument, use `db_token` per the translation implemented
        by the `Command.to_opt_name()` method.
        """
        return self._args_dict.get(arg_name)

    @classmethod
    def to_opt_name(cls, arg_name):
        """Convert a command line argument name to the option name convention

        Convert a command line argument to an option name which can be used as
        a Python attribute in the same way as `argparse` adds options to a
        namespace.  For example, `--db-token` gets convereted to `db_token`.
        """
        return arg_name.strip('-').replace('-', '_')


class Options:
    """Options based on user settings with CLI override."""

    def __init__(self, path, command, cli_args, section=None):
        """An Options object provides key/value pairs via its attributes.

        The options are first loaded from a settings file using the
        `configparser` module.  Then when getting an object attribute, the name
        is first looked up in the command line arguments so that they take
        precendence over the settings file.  Conversely, any command line
        argument can have a default value set in the settings file.

        Arguments that have a `section` attribute can only be defined in the
        settings file under the section that matches the specification.  For
        example, with `('db', 'db_config')`, the option can only be defined in
        a section called `db:<db-config-name>` with `db-config-name` the value
        passed in `db_config`, or in the `--db-config` command line argument.

        *path* is the path to the config file, if not provided it will be
                looked up in the following order:
                1) from the `KCI_SETTINGS` environment variable
                2) look for following files in order:
                     kernelci.toml, ~/.config/kernelci/kernelci.toml,
                     /etc/kernelci/kernelci.toml, kernelci.conf,
                     ~/.config/kernelci/kernelci.conf,
                     /etc/kernelci/kernelci.conf

        *command* is a `Command` object for the command being run

        *cli_args* is an object with command line arguments as produced by
                   argparse

        *section* is a section name to use in the settings file, to provide a
                  way to have default values for each CLI tool
        """
        self._deprecated_settings = False
        if path is None:
            path = os.environ.get('KCI_SETTINGS')

        if path is None:
            default_paths = [
                'kernelci.toml',
                os.path.expanduser('~/.config/kernelci/kernelci.toml'),
                '/etc/kernelci/kernelci.toml',
                'kernelci.conf',
                os.path.expanduser('~/.config/kernelci/kernelci.conf'),
                '/etc/kernelci/kernelci.conf',
            ]
            for default_path in default_paths:
                if os.path.exists(default_path):
                    path = default_path
                    break

        # If path is set, means it is either retrieved from KCI_SETTINGS
        # environment variable or set by --settings option. In both cases,
        # check if the file exists. If not, raise FileNotFoundError, so we are
        # aware file is missing.
        # If path is not set, this means "default" - it is permitted that
        # settings file does not exist, it will appear as empty dict.
        if path and not os.path.exists(path):
            raise FileNotFoundError(f"Settings file not found: {path}")

        if path and path.endswith('.conf'):
            self._deprecated_settings = True

        if self._deprecated_settings:
            print("Warning: user settings file format '.conf' will soon be \
deprecated. Please use '.toml' file format and provide 'kernelci.toml' file \
instead.", file=sys.stderr)
            self._settings = configparser.ConfigParser()
        else:
            self._settings = {}

        if path and os.path.exists(path):
            if self._deprecated_settings:
                self._settings.read(path)
            else:
                self._settings = toml.load(path)

        if not self._deprecated_settings:
            self._default_section = self._settings.get('DEFAULT')

        self._command = command
        self._cli_args = cli_args
        self._section = section

    def __getattr__(self, name):
        return self.get(name)

    @property
    def command(self):
        """The Command object associated with this instance."""
        return self._command

    def get(self, option, as_list=False):
        """Get an option value.

        This is an explicit call to get an option value, which can also be done
        by accessing an object attribute i.e. `self.option`.

        *option* is the name of the option to look up

        *as_list* is to always get the result as a list even if there is only
                  one value, for options that can have multiple values
                  separated by some spaces
        """
        value = getattr(self._cli_args, option, None)
        if value:
            return value
        opt_data = self._command.get_arg_data(option)
        section_data = opt_data.get('section') if opt_data else None
        if section_data:
            section_name, section_config_option = section_data
            section_config = self.get(section_config_option)
            if not section_config:
                return None
            section = (section_name, section_config)
        else:
            section = self._section
        return self.get_from_section(section, option, as_list)

    def get_from_section(self, section, option, as_list=False):
        """Get an option from an arbitrary section

        While the .get() method will use other arguments such as --api-config
        to look up the matching section in the settings file, this makes it
        possible to retrieve values from any arbitrary section.  It is
        primarily useful when the code needs to get options from multiple
        sections, for example to iterate over all the runtimes.

        *section* is the name of the section in the settings
        *option* is the name of the option within that sectino
        *as_list* is like for .get() for options with multiple values
        """
        if self._deprecated_settings:
            if isinstance(section, tuple):
                section = ':'.join([section[0], section[1]])
            if not self._settings.has_option(section, option):
                return None
            value = self._settings.get(section, option).split()
            if not as_list and len(value) == 1:
                value = value[0]
        else:
            value = None
            if isinstance(section, tuple):
                section_data = self._settings.get(
                    section[0], {}).get(section[1])
            else:
                section_data = self._settings.get(section)
            if section_data:
                value = section_data.get(option)
            if value is None and self._default_section:
                value = self._default_section.get(option)
        return value

    def get_missing_args(self):
        """Get a list of any missing required arguments."""
        if not self.command.args:
            return None
        missing_args = []
        for arg_name in (arg['name'] for arg in self.command.args):
            opt_name = self.command.to_opt_name(arg_name)
            if self.get(opt_name) is None:
                missing_args.append(arg_name)
        return missing_args

    def get_yaml_configs(self):
        """Get a list of all the YAML configuration paths."""
        config_paths = []
        if self.yaml_config:
            config_paths.append(self.yaml_config)
        if self.extra_config:
            config_paths.extend(self.extra_config)
        return config_paths


def make_parser(title):
    """Helper to make a parser object from argparse.

    *title* is the title of the parser
    """
    parser = argparse.ArgumentParser(title)
    parser.add_argument(
        "--yaml-config",
        help="Path to the Kernel CI directory with YAML config files",
    )
    parser.add_argument(
        "--extra-config",
        action='append',
        default=[],
        help="Path to additional YAML site config files",
    )
    parser.add_argument(
        "--settings",
        help="Path to the settings file",
    )
    return parser


def add_subparsers(parser, glob):
    """Helper to add a sub-parser to add sub-commands

    All the global attributes from `glob` starting with `cmd_` are added as
    sub-commands to the parser.

    *parser* is the main parser object from argparse
    *glob* is the globals dictionary
    """
    sub_parsers = parser.add_subparsers(title="Commands",
                                        help="List of available commands")
    for k in list(glob.keys()):
        split = k.split('cmd_')
        if len(split) == 2:
            obj = glob.get(k)
            if issubclass(obj, Command):
                cmd_name = split[1]
                obj(sub_parsers, cmd_name)


def parse_args_with_parser(parser, glob, args=None):
    """Parse the command line arguments with a provided parser

    *parser* is an `ArgumentParser` instance used to parse the command line.

    *glob* is the dictionary with all the global attributes where to look for
           commands starting with `cmd_`

    *args* is the list of arguments to parse.  When not provided, the default
           set of arguments from sys.argv will be used as per argparse's
           implementation
    """
    add_subparsers(parser, glob)
    args = parser.parse_args(args)
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    return args


def make_options(args, prog):
    """Return an Options object using existing arguments

    *args* is the arguments as returned by `argparse`
    *prog* is the name of the command line program
    """
    opts = Options(args.settings, args.func, args, prog)
    missing_args = opts.get_missing_args()
    if missing_args:
        print("The following arguments or settings are required: "
              + ', '.join(missing_args))
        sys.exit(1)
    return opts


def parse_opts(prog, glob, args=None):
    """Return an Options object with command line arguments and settings

    This will create a parser and automatically add the sub-commands from the
    global attributes `glob` and parse the arguments.  Thhen it will create an
    `Options` object using any KernelCI settings file found.

    *prog* is the command line program name

    *glob* is the dictionary with all the global attributes where to look for
           commands starting with `cmd_`

    *args* is the list of arguments to parse, or by default all the command
           line arguments from sys.argv
    """
    parser = make_parser(prog)
    args = parse_args_with_parser(parser, glob, args)
    return make_options(args, prog)


def sub_main(name, glob, args=None):
    """Standard main function for sub-commands

    This can be called as a default implementation for a sub-command main
    function.  It will load the YAML config and settings, call the command and
    exit with a status code based on the returned value from the command.

    *name* is passed to the parser as the command name for the help message
    *glob* is a dictionary with global variables, typically globals()
    *args* is an optional list of arguments to override sys.argv
    """
    opts = parse_opts(name, glob, args=args)
    configs = kernelci.config.load(opts.get_yaml_configs())
    status = opts.command(configs, opts)
    sys.exit(0 if status is True else 1)
