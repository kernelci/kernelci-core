# Copyright (C) 2014 Linaro Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The model that represents a boot document in the mongodb collection."""

import types

from models.base import BaseDocument
from utils import LOG

BOOT_COLLECTION = 'boot'


class BootDocument(BaseDocument):
    """Model for a boot document.

    Each document holds a list of boards that have been tested. Each board
    is a dictionary with at least the following values:

    board - the board name
    time - time taken to run the test, measured as seconds passed from the
        epoch time
    status - the status of the boot test
    warnings - the number of warnings
    """

    ID_FORMAT = 'boot-%(job)s-%(kernel)s-%(defconfig)s'

    def __init__(self, name, job=None, kernel=None, defconfig=None):
        super(BootDocument, self).__init__(name)

        self._job = job
        self._kernel = kernel
        self._defconfig = defconfig
        self._created = None
        self._boards = []

    @property
    def collection(self):
        return BOOT_COLLECTION

    @property
    def job(self):
        return self._job

    @job.setter
    def job(self, value):
        self._job = value

    @property
    def kernel(self):
        return self._kernel

    @kernel.setter
    def kernel(self, value):
        self._kernel = value

    @property
    def defconfig(self):
        return self._defconfig

    @defconfig.setter
    def defconfig(self, value):
        self._defconfig = value

    @property
    def created(self):
        """Date of last modification of the boot log file."""
        return self._created

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def boards(self):
        return self._boards

    @boards.setter
    def boards(self, value):
        if not isinstance(value, types.ListType):
            if isinstance(value, types.DictionaryType):
                self._boards.append(value)
            else:
                LOG.error(
                    "Stored boards need to be of type Dictionary, got %s",
                    type(value)
                )
        elif isinstance(value, types.ListType):
            self._boards.extend(value)

    def to_dict(self):
        boot_dict = super(BootDocument, self).to_dict()
        boot_dict['created'] = self._created
        boot_dict['job'] = self._job
        boot_dict['kernel'] = self._kernel
        boot_dict['defconfig'] = self._defconfig
        boot_dict['boards'] = self._boards
        return boot_dict
