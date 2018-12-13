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
            self,
            board,
            job,
            kernel,
            defconfig,
            lab_name,
            git_branch,
            build_environment,
            defconfig_full,
            arch):
        """A new BootDocument.

        :param board: The name of the board.
        :type board: string
        :param job: The job value.
        :type job: string
        :param kernel: The kernel value.
        :type kernel: string
        :param defconfig: The defconfig value.
        :type defconfig: string
        :param lab_name: The user readable ID of the lab.
        :type lab_name: string
        :param defconfig_full: The full value of the defconfig when it contains
        fragments. Default to the same 'defconfig' value.
        :type defconfig_full: string
        :param arch: The architecture type.
        :type arch: string
        """
        self._created_on = None
        self._id = None
        self._version = None

        self.arch = arch
        self.board = board
        self.defconfig = defconfig
        self.defconfig_full = defconfig_full or defconfig
        self.git_branch = git_branch
        self.job = job
        self.kernel = kernel
        self.lab_name = lab_name
        self.build_environment = build_environment

        self.board_instance = None
        self.boot_job_id = None
        self.boot_job_path = None
        self.boot_job_url = None
        self.boot_log = None
        self.boot_log_html = None
        self.boot_result_description = None
        self.bootloader = None
        self.bootloader_version = None
        self.build_id = None
        self.chainloader = None
        self.compiler = None
        self.compiler_version = None
        self.compiler_version_ext = None
        self.compiler_version_full = None
        self.cross_compile = None
        self.device_type = None
        self.dtb = None
        self.dtb_addr = None
        self.dtb_append = None
        self.endian = None
        self.fastboot = False
        self.fastboot_cmd = None
        self.file_server_resource = None
        self.file_server_url = None
        self.filesystem = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.initrd = None
        self.initrd_addr = None
        self.job_id = None
        self.kernel_image = None
        self.kernel_image_size = None
        self.load_addr = None
        self.mach = None
        self.metadata = {}
        self.qemu = None
        self.qemu_command = None
        self.retries = 0
        self.status = None
        self.time = 0
        self.uimage = None
        self.uimage_addr = None
        self.warnings = 0

    @property
    def collection(self):
        return models.BOOT_COLLECTION

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
            models.BOOTLOADER_TYPE_KEY: self.bootloader,
            models.BOOTLOADER_VERSION_KEY: self.bootloader_version,
            models.BOOT_JOB_ID_KEY: self.boot_job_id,
            models.BOOT_JOB_PATH_KEY: self.boot_job_path,
            models.BOOT_JOB_URL_KEY: self.boot_job_url,
            models.BOOT_LOG_HTML_KEY: self.boot_log_html,
            models.BOOT_LOG_KEY: self.boot_log,
            models.BOOT_RESULT_DESC_KEY: self.boot_result_description,
            models.BUILD_ENVIRONMENT_KEY: self.build_environment,
            models.BUILD_ID_KEY: self.build_id,
            models.CHAINLOADER_TYPE_KEY: self.chainloader,
            models.COMPILER_KEY: self.compiler,
            models.COMPILER_VERSION_EXT_KEY: self.compiler_version_ext,
            models.COMPILER_VERSION_FULL_KEY: self.compiler_version_full,
            models.COMPILER_VERSION_KEY: self.compiler_version,
            models.CROSS_COMPILE_KEY: self.cross_compile,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DEVICE_TYPE_KEY: self.device_type,
            models.DTB_ADDR_KEY: self.dtb_addr,
            models.DTB_APPEND_KEY: self.dtb_append,
            models.DTB_KEY: self.dtb,
            models.ENDIANNESS_KEY: self.endian,
            models.FASTBOOT_CMD_KEY: self.fastboot_cmd,
            models.FASTBOOT_KEY: self.fastboot,
            models.FILESYSTEM_TYPE_KEY: self.filesystem,
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
            models.KERNEL_IMAGE_SIZE_KEY: self.kernel_image_size,
            models.KERNEL_KEY: self.kernel,
            models.LAB_NAME_KEY: self.lab_name,
            models.LOAD_ADDR_KEY: self.load_addr,
            models.MACH_KEY: self.mach,
            models.METADATA_KEY: self.metadata,
            models.QEMU_COMMAND_KEY: self.qemu_command,
            models.QEMU_KEY: self.qemu,
            models.RETRIES_KEY: self.retries,
            models.STATUS_KEY: self.status,
            models.TIME_KEY: self.time,
            models.UIMAGE_ADDR_KEY: self.uimage_addr,
            models.UIMAGE_KEY: self.uimage,
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
                git_branch = doc_pop(models.GIT_BRANCH_KEY)
                defconfig_full = doc_pop(models.DEFCONFIG_FULL_KEY, None)
                arch = doc_pop(models.ARCHITECTURE_KEY)
                build_environment = doc_pop(models.BUILD_ENVIRONMENT_KEY)

                boot_doc = BootDocument(
                    board,
                    job,
                    kernel,
                    defconfig,
                    lab_name,
                    git_branch,
                    build_environment,
                    defconfig_full=defconfig_full, arch=arch
                )

                boot_doc.id = boot_id

                for key, val in local_obj.iteritems():
                    setattr(boot_doc, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                boot_doc = None

        return boot_doc
