# Copyright (C) 2022 Collabora Limited
# Author: Alexandra Pereira <alexandra.pereira@collabora.com>
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

import yaml

from kernelci.config.base import YAMLObject


class Email(YAMLObject):
    def __init__(self, email_env, email_send_to):
        self._email_env = email_env
        self._email_send_to = email_send_to

    @classmethod
    def from_yaml(cls, email_env, kw):
        return cls(email_env, **kw)

    @property
    def email_env(self):
        return self._email_env

    @property
    def email_send_to(self):
        return self._email_send_to


def from_yaml(data):
    emails = {
        name: Email.from_yaml(name, email_config)
        for name, email_config in data.get('email_configs', {}).items()
    }

    return {
        'email_configs': emails,
    }
