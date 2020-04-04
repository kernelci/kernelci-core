# Copyright (C) 2020 Google LLC
# Author: Heidi Fahim <heidifahim@google.com>
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

from jinja2 import Environment, FileSystemLoader
import os
import subprocess

from kernelci.lab import LabAPI


class SHELL(LabAPI):

    shell_script = 'shell_lab.sh'

    def connect(self, user=None, token=None):
        print('User and Token not required for a SHELL lab. '
              'Skipping connection step.')

    def generate(self, params, target, plan, callback_opts, args=None):
        # shell command variable that will be modified depending on the
        # test_plan
        shell_command = ''
        if plan.base_name == 'kunit':
            run_path = os.path.realpath(os.path.join(target,
                                                     params['run_path']))
            out_json = (os.path.realpath(args.output) if args and args.output
                        else 'stdout')
            config = params['config']
            shell_command = '%s run --json=%s %s' % (run_path,
                                                     out_json,
                                                     config)
            with open(self.shell_script, 'w') as file:
                file.write(shell_command)
        print('Shell commands generated and saved to %s' %
              os.path.realpath(file.name))
        return file.name

    def submit(self, job):
        return subprocess.call([job], shell=True)


def get_api(lab):
    """Get a SHELL lab API object"""
    return SHELL(lab)
