# Copyright (C) 2018, 2019 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import argparse
import configparser
import os.path


# -----------------------------------------------------------------------------
# Standard arguments that can be used in sub-commands
#

class Args:
    """A list of all the common command line argument options

    All the members of this class are arguments that can be reused in various
    command line tools.  They are dictionaries with at least a `name`
    attribute, and all the other ones are passed as keyword arguments to the
    add_argument() method of the parser object from argparse.  There should
    also always be a `help` attribute, as this is needed by the Command class.
    """
    SECTION_DB = ('db', 'db_config')
    SECTION_LAB = ('lab', 'lab_config')

    arch = {
        'name': '--arch',
        'help': "CPU architecture name",
    }

    api = {
        'name': '--api',
        'help': "Backend API URL",
        'section': SECTION_DB,
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
        'help': "Dataset to include in a lab callback",
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

    lab_config = {
        'name': '--lab-config',
        'help': 'Test lab config name',
    }

    lab_json = {
        'name': '--lab-json',
        'help': "Path to a JSON file with lab-specific info",
        'section': SECTION_LAB,
    }

    lab_token = {
        'name': '--lab-token',
        'help': "Test lab token",
        'section': SECTION_LAB,
    }

    log = {
        'name': '--log',
        'help': "Path to log file",
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
        'choices': ('debos', 'buildroot')
    }

    storage = {
        'name': '--storage',
        'help': "Storage URL",
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
        'help': "Upload path on Storage where rootfs stored",
    }

    url = {
        'name': '--url',
        'help': "Kernel sources download URL",
    }

    user = {
        'name': '--user',
        'help': "Test lab user name",
        'section': SECTION_LAB,
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


class Command:
    """A command helper class.

    It contains several class attributes:

    *help* is the help message passed to tbe sub-parser
    *args* is a list of required arguments dictionaries to add to the parser
    *opt_args* is a list of optional arguments to add to the parser
    """

    help = None
    args = None
    opt_args = None

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
            raise AttributeError("Missing help message for {}".format(name))
        self._parser = sub_parser.add_parser(name, help=self.help)
        for arg_list in [self.args, self.opt_args]:
            if arg_list:
                for arg in arg_list:
                    self._add_arg(arg)
        self._parser.set_defaults(func=self)
        self._args_dict = dict()
        for arg_list in [self.args, self.opt_args]:
            if arg_list:
                self._args_dict.update({
                    self.to_opt_name(arg['name']): arg
                    for arg in arg_list
                })

    def __call__(self, *args, **kw):
        raise NotImplementedError("Command not implemented")

    def _add_arg(self, arg):
        kw = dict(arg)
        arg_name = kw.pop('name')
        kw.pop('section', None)
        self._parser.add_argument(arg_name, **kw)

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

        *path* is the path to the config file, which by default is
                `kernelci.conf` or
               `~/.config/kernelci/kernelci.conf` or
               `/etc/kernelci/kernelci.conf`

        *command* is a `Command` object for the command being run

        *cli_args* is an object with command line arguments as produced by
                   argparse

        *section* is a section name to use in the settings file, to provide a
                  way to have default values for each CLI tool

        """
        if path is None:
            default_paths = [
                'kernelci.conf',
                os.path.expanduser('~/.config/kernelci/kernelci.conf'),
                '/etc/kernelci/kernelci.conf',
            ]
            for path in default_paths:
                if os.path.exists(path):
                    break
        self._settings = configparser.ConfigParser()
        if path and os.path.exists(path):
            self._settings.read(path)
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
            section = ':'.join([section_name, section_config])
        else:
            section = self._section
        if not self._settings.has_option(section, option):
            return None
        value = self._settings.get(section, option).split()
        if not as_list and len(value) == 1:
            value = value[0]
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


def make_parser(title, default_config_path):
    """Helper to make a parser object from argparse.

    *title* is the title of the parser
    *default_config_path* is the default YAML config directory to use
    """
    parser = argparse.ArgumentParser(title)
    parser.add_argument("--yaml-config", default=default_config_path,
                        help="Path to the directory with YAML config files")
    parser.add_argument("--settings",
                        help="Path to the settings file")
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


def parse_args_with_parser(parser, glob):
    """Parse the command line arguments with a provided parser

    *glob* is the dictionary with all the global attributes where to look for
           commands starting with `cmd_`

    *parser* is an `ArgumentParser` instance used to parse the command line.
    """
    add_subparsers(parser, glob)
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        exit(1)
    return args


def make_options(args, prog):
    """Return an Options object using existing arguments

    *args* is the arguments as returned by `argparse`
    *prog* is the name of the command line program
    """
    opts = Options(args.settings, args.func, args, prog)
    missing_args = opts.get_missing_args()
    if missing_args:
        print("The following arguments or settings are required: {}".format(
            ', '.join(missing_args)))
        exit(1)
    return opts


def parse_opts(prog, glob, default_config_path="config/core"):
    """Return an Options object with command line arguments and settings

    This will create a parser and automatically add the sub-commands from the
    global attributes `glob` and parse the arguments.  Thhen it will create an
    `Options` object using any KernelCI settings file found.

    *prog* is the command line program name

    *default_config_path* is the name of the default YAML configuration
                          directory to use with the command line utility

    *glob* is the dictionary with all the global attributes where to look for
           commands starting with `cmd_`
    """
    parser = make_parser(prog, default_config_path)
    args = parse_args_with_parser(parser, glob)
    return make_options(args, prog)
