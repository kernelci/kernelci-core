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
import urlparse
import xmlrpclib


class LabAPI(object):
    """Remote API to a test lab"""

    def __init__(self, config, user, token):
        """A test lab API object can be used to remotely interact with a lab

        *config* is a kernelci.config.lab.Lab object
        *user* is the name of the user to connect to the lab
        *token* is the token associated with the user to connect to the lab
        """
        self._config = config
        self._connect(user, token)
        self._devices = None

    @property
    def config(self):
        return self._config

    @property
    def devices(self):
        if self._devices is None:
            self._devices = self._get_devices()
        return self._devices

    def _connect(self, user=None, token=None):
        if user and token:
            url = urlparse.urlparse(self.config.url)
            api_url = "{scheme}://{user}:{token}@{loc}{path}".format(
                scheme=url.scheme, user=user, token=token,
                loc=url.netloc, path=url.path)
        else:
            api_url = self.config.url
        self._server = xmlrpclib.ServerProxy(api_url)

    def _get_devices(self):
        return list()

    def import_devices(self, data):
        self._devices = data

    def device_type_online(self, device_type_name):
        return True

    def job_file_name(self, params):
        return params['name']

    def match(self, filter_data):
        return self.config.match(filter_data)

    def generate(self, params, target, plan, callback_opts):
        raise NotImplementedError("Lab.generate() is required")

    def submit(self, job):
        raise NotImplementedError("Lab.submit() is required")


def get_api(lab, user, token):
    """Get the LabAPI object for a given lab config.

    *lab* is a kernelci.config.lab.Lab object
    *user* is the name of the user to connect to the remote lab
    *token* is the associated token to connect to the remote lab
    """
    m = importlib.import_module('.'.join(['kernelci', 'lab', lab.lab_type]))
    return m.get_api(lab, user, token)
