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
    BOOT_LOG_KEY,
    DEFCONFIG_KEY,
    DTB_ADDR_KEY,
    DTB_KEY,
    ENDIANNESS_KEY,
    INITRD_ADDR_KEY,
    JOB_ID_KEY,
    JOB_KEY,
    KERNEL_IMAGE_KEY,
    KERNEL_KEY,
    LOAD_ADDR_KEY,
    METADATA_KEY,
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
        self._boot_log = None
        self._initrd_addr = None
        self._load_addr = None
        self._kernel_image = None
        self._dtb_addr = None
        self._dtb = None
        self._endianness = None
        self._metadata = None

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
    def boot_log(self):
        """The log of this board."""
        return self._boot_log

    @boot_log.setter
    def boot_log(self, value):
        self._boot_log = value

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

    @property
    def initrd_addr(self):
        return self._initrd_addr

    @initrd_addr.setter
    def initrd_addr(self, value):
        self._initrd_addr = value

    @property
    def load_addr(self):
        """The load_addr."""
        return self._load_addr

    @load_addr.setter
    def load_addr(self, value):
        self._load_addr = value

    @property
    def dtb_addr(self):
        return self._dtb_addr

    @dtb_addr.setter
    def dtb_addr(self, value):
        self._dtb_addr = value

    @property
    def dtb(self):
        """The dtb file of this boot document."""
        return self._dtb

    @dtb.setter
    def dtb(self, value):
        self._dtb = value

    @property
    def kernel_image(self):
        """The kernel image used to boot."""
        return self._kernel_image

    @kernel_image.setter
    def kernel_image(self, value):
        self._kernel_image = value

    @property
    def endianness(self):
        return self._endianness

    @endianness.setter
    def endianness(self, value):
        self._endianness = value

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def to_dict(self):
        boot_dict = super(BootDocument, self).to_dict()
        boot_dict[BOARD_KEY] = self._board
        boot_dict[TIME_KEY] = self._time
        boot_dict[JOB_KEY] = self._job
        boot_dict[KERNEL_KEY] = self._kernel
        boot_dict[DEFCONFIG_KEY] = self._defconfig
        boot_dict[STATUS_KEY] = self._status
        boot_dict[BOOT_LOG_KEY] = self._boot_log
        boot_dict[WARNINGS_KEY] = self._warnings
        boot_dict[JOB_ID_KEY] = self._job_id
        boot_dict[KERNEL_IMAGE_KEY] = self._kernel_image
        boot_dict[LOAD_ADDR_KEY] = self._load_addr
        boot_dict[INITRD_ADDR_KEY] = self._initrd_addr
        boot_dict[DTB_KEY] = self._dtb
        boot_dict[DTB_ADDR_KEY] = self._dtb_addr
        boot_dict[ENDIANNESS_KEY] = self._endianness
        boot_dict[METADATA_KEY] = self._metadata
        return boot_dict
