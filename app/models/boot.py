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

import models
import models.base as modb


# pylint: disable=too-many-public-methods
class BootDocument(modb.BaseDocument):
    """Model for a boot document.

    Each document is a single booted board.
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    def __init__(self, board, job, kernel, defconfig, lab_id):
        """A new BootDocument.

        :param board: The name of the board.
        :type board: str
        :param job: The name of the job.
        :type job: str
        :param kernel: The name of the kernel.
        :type kernel: str
        :param defconfig: The name of the defconfig.
        :type defconfig: str
        :param lab_id: The user readable ID of the lab.
        :type lab_id: str
        """
        self._board = board
        self._name = models.BOOT_DOCUMENT_NAME % {
            models.BOARD_KEY: board,
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.DEFCONFIG_KEY: defconfig,
        }
        self._lab_id = lab_id
        self._job = job

        self._id = None
        self._created_on = None

        self._kernel = kernel
        self._defconfig = defconfig

        self._metadata = {}
        self._job_id = None
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
        self._fastboot = None
        self._boot_log_html = None
        self._boot_result_description = None
        self._retries = None

    @property
    def collection(self):
        return models.BOOT_COLLECTION

    @property
    def name(self):
        """The name of the boot report."""
        return self._name

    @property
    def id(self):
        """The ID of this object as returned by mongodb."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the ID of this object with the ObjectID from mongodb.

        :param value: The ID of this object.
        :type value: str
        """
        self._id = value

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
        """Set the status of this board document.

        :param value: The status to set.
        :type value: str
        """
        self._status = value

    @property
    def boot_log(self):
        """The URI of the log of this board in txt format."""
        return self._boot_log

    @boot_log.setter
    def boot_log(self, value):
        """Set the boot log txt URI.

        :param value: The URI of the board log.
        :type value: str
        """
        self._boot_log = value

    @property
    def time(self):
        """The time it took this board to boot.

        Represented as the time passed after the epoch time.
        """
        return self._time

    @time.setter
    def time(self, value):
        """Set the time it took to boot this board.

        :param value: The boot time to set.
        :type value: datetime
        """
        self._time = value

    @property
    def warnings(self):
        """The number of warnings associated with this board."""
        return self._warnings

    @warnings.setter
    def warnings(self, value):
        """Set the number of warnings associated with this board.

        :param value: The number of warnings.
        :type value: int
        """
        self._warnings = value

    @property
    def job_id(self):
        """The ID of the Job document associated with this boot."""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        """Set the job ID document associated.

        :param value: The ID of the associated job.
        :type value: str
        """
        self._job_id = value

    @property
    def initrd_addr(self):
        """The initrd address."""
        return self._initrd_addr

    @initrd_addr.setter
    def initrd_addr(self, value):
        """Set the initrd address."""
        self._initrd_addr = value

    @property
    def load_addr(self):
        """The load address."""
        return self._load_addr

    @load_addr.setter
    def load_addr(self, value):
        """Set the load address."""
        self._load_addr = value

    @property
    def dtb_addr(self):
        """The dtb address."""
        return self._dtb_addr

    @dtb_addr.setter
    def dtb_addr(self, value):
        """Set the dtb address."""
        self._dtb_addr = value

    @property
    def dtb(self):
        """The dtb file of this boot document."""
        return self._dtb

    @dtb.setter
    def dtb(self, value):
        """Set the dtb file value."""
        self._dtb = value

    @property
    def kernel_image(self):
        """The kernel image used to boot."""
        return self._kernel_image

    @kernel_image.setter
    def kernel_image(self, value):
        """Set the URI of the kernel image used to boot."""
        self._kernel_image = value

    @property
    def endianness(self):
        """The endianness of the board."""
        return self._endianness

    @endianness.setter
    def endianness(self, value):
        """Set the endianness of the board."""
        self._endianness = value

    @property
    def fastboot(self):
        """If the board is fastboot."""
        return self._fastboot

    @fastboot.setter
    def fastboot(self, value):
        """Set if the board is fastboot."""
        self._fastboot = value

    @property
    def boot_log_html(self):
        """The board boot log in HTML format."""
        return self._boot_log_html

    @boot_log_html.setter
    def boot_log_html(self, value):
        """Set the URI of the board boot log in HTML format."""
        self._boot_log_html = value

    @property
    def retries(self):
        """How many times the boot process has been retried."""
        return self._retries

    @retries.setter
    def retries(self, value):
        """Set the retries value."""
        self._retries = value

    @property
    def metadata(self):
        """A free form object that stores values not defined in the model."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set the metadata value."""
        self._metadata = value

    @property
    def lab_id(self):
        """Get the lab ID value of this boot report."""
        return self._lab_id

    @lab_id.setter
    def lab_id(self, value):
        """Set the lab ID value."""
        self._lab_id = value

    @property
    def boot_result_description(self):
        """Get the boot result description."""
        return self._boot_result_description

    @boot_result_description.setter
    def boot_result_description(self, value):
        """Set the boot result description.

        :param value: The description of the boot status.
        :type value: str
        """
        self._boot_result_description = value

    @property
    def created_on(self):
        """When this lab object was created."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this lab object.

        :param value: The lab creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

    def to_dict(self):
        boot_dict = {
            models.NAME_KEY: self.name,
            models.BOARD_KEY: self.board,
            models.TIME_KEY: self.time,
            models.JOB_KEY: self.job,
            models.KERNEL_KEY: self.kernel,
            models.DEFCONFIG_KEY: self.defconfig,
            models.STATUS_KEY: self.status,
            models.BOOT_LOG_KEY: self.boot_log,
            models.WARNINGS_KEY: self.warnings,
            models.JOB_ID_KEY: self.job_id,
            models.KERNEL_IMAGE_KEY: self.kernel_image,
            models.LOAD_ADDR_KEY: self.load_addr,
            models.INITRD_ADDR_KEY: self.initrd_addr,
            models.DTB_KEY: self.dtb,
            models.DTB_ADDR_KEY: self.dtb_addr,
            models.ENDIANNESS_KEY: self.endianness,
            models.METADATA_KEY: self.metadata,
            models.FASTBOOT_KEY: self.fastboot,
            models.BOOT_LOG_HTML_KEY: self.boot_log_html,
            models.BOOT_RESULT_DESC_KEY: self.boot_result_description,
            models.RETRIES_KEY: self.retries,
            models.LAB_ID_KEY: self.lab_id,
            models.CREATED_KEY: self.created_on,
        }

        if self.id:
            boot_dict[models.ID_KEY] = self.id

        return boot_dict

    @staticmethod
    def from_json(json_obj):
        return None
