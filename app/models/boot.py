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

import copy
import types

import models
import models.base as modb


# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
class BootDocument(modb.BaseDocument):
    """Model for a boot document.

    Each document is a single booted board.
    """

    def __init__(
            self, board, job, kernel, defconfig, lab_name,
            defconfig_full=None, arch=models.ARM_ARCHITECTURE_KEY):
        """A new BootDocument.

        :param board: The name of the board.
        :type board: str
        :param job: The name of the job.
        :type job: str
        :param kernel: The name of the kernel.
        :type kernel: str
        :param defconfig: The name of the defconfig.
        :type defconfig: str
        :param lab_name: The user readable ID of the lab.
        :type lab_name: str
        """

        doc_name = models.BOOT_DOCUMENT_NAME % {
            models.BOARD_KEY: board,
            models.DEFCONFIG_KEY: defconfig_full or defconfig,
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.ARCHITECTURE_KEY: arch
        }

        self._created_on = None
        self._id = None
        self._name = doc_name
        self._version = None

        self._arch = arch
        self._board = board
        self._defconfig = defconfig
        self._defconfig_full = defconfig_full or defconfig
        self._job = job
        self._kernel = kernel
        self._lab_name = lab_name
        self.board_instance = None
        self.boot_log = None
        self.boot_log_html = None
        self.boot_result_description = None
        self.defconfig_id = None
        self.dtb = None
        self.dtb_addr = None
        self.dtb_append = None
        self.endian = None
        self.fastboot = False
        self.fastboot_cmd = None
        self.file_server_resource = None
        self.file_server_url = None
        self.git_branch = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.initrd = None
        self.initrd_addr = None
        self.job_id = None
        self.kernel_image = None
        self.load_addr = None
        self.metadata = {}
        self.retries = 0
        self.status = None
        self.time = 0
        self.warnings = 0

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
    def arch(self):
        """The architecture of the board."""
        return self._arch

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
    def defconfig_full(self):
        """The full value of the defconfig, with fragments."""
        return self._defconfig_full

    @defconfig_full.setter
    def defconfig_full(self, value):
        """Set the defconfig full name."""
        self._defconfig_full = value

    @property
    def lab_name(self):
        """Get the lab ID value of this boot report."""
        return self._lab_name

    @lab_name.setter
    def lab_name(self, value):
        """Set the lab ID value."""
        self._lab_name = value

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

    @property
    def version(self):
        """The version of this document schema."""
        return self._version

    @version.setter
    def version(self, value):
        """The version of this document schema."""
        self._version = value

    def to_dict(self):
        boot_dict = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BOARD_INSTANCE_KEY: self.board_instance,
            models.BOARD_KEY: self.board,
            models.BOOT_LOG_HTML_KEY: self.boot_log_html,
            models.BOOT_LOG_KEY: self.boot_log,
            models.BOOT_RESULT_DESC_KEY: self.boot_result_description,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full,
            models.DEFCONFIG_ID_KEY: self.defconfig_id,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DTB_ADDR_KEY: self.dtb_addr,
            models.DTB_APPEND_KEY: self.dtb_append,
            models.DTB_KEY: self.dtb,
            models.ENDIANNESS_KEY: self.endian,
            models.FASTBOOT_CMD_KEY: self.fastboot_cmd,
            models.FASTBOOT_KEY: self.fastboot,
            models.FILE_SERVER_RESOURCE_KEY: self.file_server_resource,
            models.FILE_SERVER_URL_KEY: self.file_server_url,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_URL_KEY: self.git_url,
            models.INITRD_ADDR_KEY: self.initrd_addr,
            models.INITRD_KEY: self.initrd,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KERNEL_IMAGE_KEY: self.kernel_image,
            models.KERNEL_KEY: self.kernel,
            models.LAB_NAME_KEY: self.lab_name,
            models.LOAD_ADDR_KEY: self.load_addr,
            models.METADATA_KEY: self.metadata,
            models.NAME_KEY: self.name,
            models.RETRIES_KEY: self.retries,
            models.STATUS_KEY: self.status,
            models.TIME_KEY: self.time,
            models.VERSION_KEY: self.version,
            models.WARNINGS_KEY: self.warnings
        }

        if self.id:
            boot_dict[models.ID_KEY] = self.id

        return boot_dict

    @staticmethod
    def from_json(json_obj):
        boot_doc = None
        if isinstance(json_obj, types.DictionaryType):
            local_obj = copy.deepcopy(json_obj)
            doc_pop = local_obj.pop

            boot_id = doc_pop(models.ID_KEY, None)
            doc_pop(models.NAME_KEY, None)

            try:
                board = doc_pop(models.BOARD_KEY)
                job = doc_pop(models.JOB_KEY)
                kernel = doc_pop(models.KERNEL_KEY)
                defconfig = doc_pop(models.DEFCONFIG_KEY)
                lab_name = doc_pop(models.LAB_NAME_KEY)
                defconfig_full = doc_pop(models.DEFCONFIG_FULL_KEY, None)
                arch = doc_pop(
                    models.ARCHITECTURE_KEY, models.ARM_ARCHITECTURE_KEY)

                boot_doc = BootDocument(
                    board, job, kernel, defconfig, lab_name,
                    defconfig_full=defconfig_full,
                    arch=arch)

                boot_doc.id = boot_id

                for key, val in local_obj.iteritems():
                    setattr(boot_doc, key, val)
            except KeyError:
                # If a mandatory key is missing, just return None.
                boot_doc = None

        return boot_doc
