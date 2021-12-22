# Copyright (C) 2019 Collabora Limited
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

import importlib
import json
import os


class LabAPI:
    """Remote API to a test lab"""

    def __init__(self, config, **kwargs):
        """A test lab API object can be used to remotely interact with a lab

        *config* is a kernelci.config.lab.Lab object
        """
        self._config = config
        self._server = self._connect(**kwargs)
        self._devices = None

    @property
    def config(self):
        return self._config

    @property
    def devices(self):
        if self._devices is None:
            self._devices = self._get_devices()
        return self._devices

    def _get_devices(self):
        return list()

    def _connect(self, *args, **kwargs):
        return None

    def import_devices(self, data):
        """Import devices information

        Import an arbitrary data structure describing the devices available in
        the lab.

        *data* is the devices data structure to import
        """
        self._devices = data

    def device_type_online(self, device_type_config):
        """Check whether a given device type is online

        Return True if the device type is online in the lab, False otherwise.

        *device_type_config* is a config.test.DeviceType object
        """
        return True

    def job_file_name(self, params):
        """Get the file name where to store the generated job definition."""
        return params['name']

    def match(self, filter_data):
        """Apply filters and return True if they match, False otherwise."""
        return self.config.match(filter_data)

    def generate(self, params, device_config, plan_config,
                 callback_opts=None, templates_path=None, db_config=None):
        """Generate a test job definition.

        *params* is a dictionary with the test parameters which can be used
             when generating a job definition using templates

        *device_config* is a DeviceType configuration object for the target
             device type

        *plan_config* is a TestPlan configuration object for the target test
             plan

        *callback_opts* is a dictionary with extra options used for callbacks

        *templates_path* is an optional argument to specify the path where the
            template files should be found, when not in the standard location

        *db_config* is a Database configuration object for the database or API
            where the results should be sent
        """
        raise NotImplementedError("Lab.generate() is required")

    def save_file(self, job, output_path, params):
        """Save a test job definition in a file.

        *job* is the job definition data
        *output_path* is the directory where the file should be saved
        *params* is a dictionary with template parameters

        Return the full path where the job definition file was saved.
        """
        file_name = self.job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        with open(output_file, 'w') as output:
            output.write(job)
        return output_file

    def submit(self, job_path):
        """Submit a test job definition in a lab."""
        raise NotImplementedError("Lab.submit() is required")


def get_api(lab, user=None, token=None, lab_json=None):
    """Get the LabAPI object for a given lab config.

    *lab* is a kernelci.config.lab.Lab object
    *user* is the name of the user to connect to the remote lab
    *token* is the associated token to connect to the remote lab
    *lab_json* is the path to a JSON file with cached lab information
    """
    m = importlib.import_module('.'.join(['kernelci', 'lab', lab.lab_type]))
    api = m.get_api(lab, user=user, token=token)
    if lab_json:
        with open(lab_json) as json_file:
            devices = json.load(json_file)['devices']
            api.import_devices(devices)
    return api
