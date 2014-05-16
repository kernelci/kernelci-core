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

"""The model that represents a defconfing document in the mongodb collection."""

from models import (
    ARCHITECTURE_KEY,
    DEFCONFIG_KEY,
    DIRNAME_KEY,
    ERRORS_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    METADATA_KEY,
    STATUS_KEY,
    WARNINGS_KEY,
)
from models.base import BaseDocument

DEFCONFIG_COLLECTION = 'defconfig'


class DefConfigDocument(BaseDocument):
    """This class represents a defconfig folder as seen on the file system."""

    ID_FORMAT = '%(job_id)s-%(defconfig)s'

    def __init__(self, name, job_id, job=None, kernel=None):
        super(DefConfigDocument, self).__init__(
            self.ID_FORMAT % {JOB_ID_KEY: job_id, DEFCONFIG_KEY: name}
        )

        self._job_id = job_id
        self._job = job
        self._kernel = kernel
        self._defconfig = None
        self._dirname = None
        self._status = None
        self._metadata = {}
        self._errors = None
        self._warnings = None
        self._arch = None

    @property
    def collection(self):
        return DEFCONFIG_COLLECTION

    @property
    def job_id(self):
        """The job ID this defconfig belogns to."""
        return self._job_id

    @property
    def job(self):
        """The job this defconfig belongs too."""
        return self._job

    @job.setter
    def job(self, value):
        """Set the job name of this defconfig."""
        self._job = value

    @property
    def kernel(self):
        """The kernel this defconfig was built against."""
        return self._kernel

    @kernel.setter
    def kernel(self, value):
        """Set the kernel of this defconfig."""
        self._kernel = value

    @property
    def metadata(self):
        """A dictionary with metadata about this defconfig."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set the metadata about this defconfig.

        :param value: A dictionary with defconfig metadata.
        """
        self._metadata = value

    @property
    def status(self):
        """The status of this defconfig built."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status.

        :param value: The status as string.
        """
        self._status = value

    @property
    def defconfig(self):
        """The defconfig name of this document."""
        return self._defconfig

    @defconfig.setter
    def defconfig(self, value):
        self._defconfig = value

    @property
    def errors(self):
        """Number of errors associated with this defconfig."""
        return self._errors

    @errors.setter
    def errors(self, value):
        self._errors = value

    @property
    def warnings(self):
        """Number of warnings associated with this defconfig."""
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        self._warnings = value

    @property
    def arch(self):
        """The architecture of this defconfig."""
        return self._arch

    @arch.setter
    def arch(self, value):
        self._arch = value

    @property
    def dirname(self):
        """The name of the directory of this defconfig."""
        return self._dirname

    @dirname.setter
    def dirname(self, value):
        self._dirname = value

    def to_dict(self):
        defconf_dict = super(DefConfigDocument, self).to_dict()
        defconf_dict[JOB_ID_KEY] = self._job_id
        defconf_dict[JOB_KEY] = self._job
        defconf_dict[KERNEL_KEY] = self._kernel
        defconf_dict[STATUS_KEY] = self._status
        defconf_dict[METADATA_KEY] = self._metadata
        defconf_dict[DEFCONFIG_KEY] = self._defconfig
        defconf_dict[WARNINGS_KEY] = self._warnings
        defconf_dict[ERRORS_KEY] = self._errors
        defconf_dict[ARCHITECTURE_KEY] = self._arch
        defconf_dict[DIRNAME_KEY] = self._dirname
        return defconf_dict
