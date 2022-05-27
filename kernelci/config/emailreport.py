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


class EmailReport(YAMLObject):
    def __init__(self, name, email_sent_to, email_from, email_subject):
        self._name = name
        self._email_send_to = email_sent_to
        self._email_from = email_from
        self._email_subject = email_subject

    @classmethod
    def from_yaml(cls, emailreport, kw):
        return cls(**kw)

    @property
    def name(self):
        return self._name

    @property
    def email_send_to(self):
        return self._email_send_to

    @property
    def email_from(self):
        return self._email_from

    @property
    def email_subject(self):
        return self._email_subject


def from_yaml(data, filters):
    email_configs = {
        name: EmailReport.from_yaml(name, email_configs)
        for name, email_configs in data.get('email_configs', {}).items()
    }

    return {
        'email_configs': email_configs,
    }
