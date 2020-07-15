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

    config = {
        'name': '--config',
        'help': "Build config name",
    }

    variant = {
        'name': '--variant',
        'help': "Build config variant name",
    }

    build_env = {
        'name': '--build-env',
        'help': "Build environment name",
    }

    storage = {
        'name': '--storage',
        'help': "Storage URL",
        'default': "https://storage.kernelci.org",
        'required': False,
    }

    api = {
        'name': '--api',
        'help': "Backend API URL",
        'default': "https://api.kernelci.org",
        'required': False,
    }

    user = {
        'name': '--user',
        'help': "User name",
    }

    token = {
        'name': '--token',
        'help': "Backend API token",
    }

    callback_id = {
        'name': '--callback-id',
        'help': "Callback identifier used to look up an authentication token",
    }

    callback_dataset = {
        'name': '--callback-dataset',
        'help': "Dataset to include in a lab callback",
        'default': 'all',
    }

    callback_type = {
        'name': '--callback-type',
        'help': "Type of callback URL",
        'default': 'kernelci',
    }

    callback_url = {
        'name': '--callback-url',
        'help': "Base URL for the callback",
    }

    jobs = {
        'name': '--jobs',
        'help': "File pattern with jobs to submit",
    }

    commit = {
        'name': '--commit',
        'help': "Git commit checksum",
    }

    describe = {
        'name': '--describe',
        'help': "Git describe",
    }

    describe_verbose = {
        'name': '--describe-verbose',
        'help': "Verbose version of git describe",
    }

    tree_name = {
        'name': '--tree-name',
        'help': "Name of a kernel tree",
    }

    tree_url = {
        'name': '--tree-url',
        'help': "URL of a kernel tree",
    }

    branch = {
        'name': '--branch',
        'help': "Name of a kernel branch in a tree",
    }

    mirror = {
        'name': '--mirror',
        'help': "Path to the local kernel git mirror",
    }

    kdir = {
        'name': '--kdir',
        'help': "Path to the kernel checkout directory",
    }

    rootfs_dir = {
        'name': '--rootfs-dir',
        'help': "Path to the rootfs images directory",
    }

    arch = {
        'name': '--arch',
        'help': "CPU architecture name",
    }

    bmeta_json = {
        'name': '--bmeta-json',
        'help': "Path to the build.json file",
    }

    dtbs_json = {
        'name': '--dtbs-json',
        'help': "Path to the dtbs.json file",
    }

    lab_json = {
        'name': '--lab-json',
        'help': "Path to a JSON file with lab-specific info",
    }

    lab = {
        'name': '--lab',
        'help': "Name of a test lab",
    }

    target = {
        'name': '--target',
        'help': "Name of a target platform",
    }

    defconfig = {
        'name': '--defconfig',
        'help': "Kernel defconfig name",
    }

    j = {
        'name': '-j',
        'help': "Number of parallel build processes",
    }

    verbose = {
        'name': '--verbose',
        'help': "Verbose output",
        'action': 'store_true',
    }

    output = {
        'name': '--output',
        'help': "Path the output directory",
    }

    install_path = {
        'name': '--install-path',
        'help':
        "Path to the install directory, or _install_ inside kdir by default",
    }

    mod_path = {
        'name': '--mod-path',
        'help':
        "Path to the installed modules, or _modules_ inside output by default",
    }

    json_path = {
        'name': '--json-path',
        'help': "Path to the JSON file",
    }

    plan = {
        'name': '--plan',
        'help': "Test plan name",
    }

    mach = {
        'name': '--mach',
        'help': "Mach name (aka SoC family)",
    }

    url = {
        'name': '--url',
        'help': "Kernel sources download URL",
    }

    filename = {
        'name': '--filename',
        'help': "Kernel sources destination filename",
        'required': False,
        'default': 'linux-src.tar.gz',
    }

    retries = {
        'name': '--retries',
        'help': 'Number of retries before download fails',
        'required': False,
        'default': 1,
        'type': int,
    }

    publish_path = {
        'name': '--publish-path',
        'help': "Relative path where build artifacts are published",
    }

    data_path = {
        'name': '--data-path',
        'help': "Path to the debos files",
    }

    upload_path = {
        'name': '--upload-path',
        'help': "Upload path on Storage where rootfs stored",
    }

    delete = {
        'name': '--delete',
        'help': "Delete the tarball after extracting",
        'action': 'store_true'
    }

    data_file = {
        'name': '--data-file',
        'help': "Path to the file with data to be submitted to storage",
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
        if self.args:
            for arg in self.args:
                self._add_arg(arg, True)
        if self.opt_args:
            for arg in self.opt_args:
                self._add_arg(arg, False)
        self._parser.set_defaults(func=self)

    def __call__(self, *args, **kw):
        raise NotImplementedError("Command not implemented")

    def _add_arg(self, arg, required=True):
        kw = dict(arg)
        arg_name = kw.pop('name')
        if required:
            kw.setdefault('required', True)
        self._parser.add_argument(arg_name, **kw)


def make_parser(title, default_yaml):
    """Helper to make a parser object from argparse.

    *title* is the title of the parser
    *default_yaml* is the default YAML config file name to use
    """
    parser = argparse.ArgumentParser(title)
    parser.add_argument("--yaml-configs", default=default_yaml,
                        help="Path to the YAML configs file")
    return parser


def add_subparser(parser, glob):
    """Helper to add a sub-parser to add sub-commands

    All the global attributes from `glob` starting with `cmd_` are added as
    sub-commands to the parser.

    *parser* is the main parser object from argparse
    *glob* is the globals dictionary
    """
    sub_parser = parser.add_subparsers(title="Commands",
                                       help="List of available commands")
    commands = dict()
    for k in list(glob.keys()):
        split = k.split('cmd_')
        if len(split) == 2:
            obj = glob.get(k)
            if issubclass(obj, Command):
                cmd_name = split[1]
                commands[cmd_name] = obj(sub_parser, cmd_name)


def parse_args(title, default_yaml, glob):
    """Helper function to parse the command line arguments

    This will create a parser and automatically add the sub-commands from the
    global attributes `glob` and return the parsed arguments.

    *title* is the parser title

    *default_yaml* is the name of the default YAML configuration file to use
                   with the command line utility

    *glob* is the dictionary with all the global attributes where to look for
           commands starting with `cmd_`
    """
    parser = make_parser(title, default_yaml)
    add_subparser(parser, glob)
    args = parser.parse_args()
    return args
