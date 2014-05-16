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

from models import (
    BOARD_KEY,
    DEFCONFIG_KEY,
    FAIL_LOG_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_KEY,
    STATUS_KEY,
    TIME_KEY,
    WARNINGS_KEY,
)
from models.base import BaseDocument
from models.job import JobDocument

BOOT_COLLECTION = 'boot'


class BootDocument(BaseDocument):
    """Model for a boot document.

    Each document is a single booted board.
    """

    ID_FORMAT = '%(board)s-%(job)s-%(kernel)s-%(defconfig)s'

    def __init__(self, board, job, kernel, defconfig):
        super(BootDocument, self).__init__(
            self.ID_FORMAT % {
                BOARD_KEY: board,
                JOB_KEY: job,
                KERNEL_KEY: kernel,
                DEFCONFIG_KEY: defconfig,
            }
        )

        self._job_id = JobDocument.ID_FORMAT % {
            JOB_KEY: job, KERNEL_KEY: kernel
        }

        self._board = board
        self._job = job
        self._kernel = kernel
        self._defconfig = defconfig
        self._time = None
        self._status = None
        self._warnings = None
        self._fail_log = []

    @property
    def collection(self):
        return BOOT_COLLECTION

    @property
    def board(self):
        """The board of this document."""
        return self._board

    @property
    def job(self):
        """The job this boot document belongs to."""
        return self._job

    @property
    def kernel(self):
        """The kernel this boot document belongs to."""
        return self._kernel

    @property
    def defconfig(self):
        """The defconfig of this boot document."""
        return self._defconfig

    @property
    def status(self):
        """The boot status of this document."""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def fail_log(self):
        """The log of this board in case it failed to boot.

        It is stored as a list of strings.
        """
        return self._fail_log

    @fail_log.setter
    def fail_log(self, value):
        self._fail_log = value

    @property
    def time(self):
        """The time it took this board to boot.

        Represented as the time passed after the epoch time.
        """
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    @property
    def warnings(self):
        """The number of warnings associated with this board."""
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        self._warnings = value

    @property
    def job_id(self):
        """The ID of the Job document associated with this boot."""
        return self._job_id

    def to_dict(self):
        boot_dict = super(BootDocument, self).to_dict()
        boot_dict[BOARD_KEY] = self._board
        boot_dict[TIME_KEY] = self._time
        boot_dict[JOB_KEY] = self._job
        boot_dict[KERNEL_KEY] = self._kernel
        boot_dict[DEFCONFIG_KEY] = self._defconfig
        boot_dict[STATUS_KEY] = self._status
        boot_dict[FAIL_LOG_KEY] = self._fail_log
        boot_dict[WARNINGS_KEY] = self._warnings
        boot_dict[JOB_ID_KEY] = self._job_id
        return boot_dict
