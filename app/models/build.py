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

"""The model that represents a build in the db."""

import copy
import types

import models
import models.base as mbase


# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
class BuildDocument(mbase.BaseDocument):
    """This class represents a build."""

    def __init__(
            self, job, kernel, defconfig, git_branch, build_environment,
            defconfig_full=None):
        """A build document.

        :param job: The job value.
        :type job: string
        :param kernel: The kernel value.
        :type kernel: string
        :param defconfig: The defconfig value.
        :type defconfig: string
        :param defconfig_full: The full value of the defconfig when it contains
        fragments. Default to the same 'defconfig' value.
        :type defconfig_full: string
        :param build_environment: The description of the build environment
        used to build the kernel_image
        :type build_environment: string
        """
        self._created_on = None
        self._id = None
        self._version = None

        self._build_platform = []
        self._metadata = {}
        self._status = None

        self.defconfig = defconfig
        self.defconfig_full = defconfig_full or defconfig
        self.job = job
        self.kernel = kernel
        self.git_branch = git_branch

        self.arch = None
        self.build_log = None
        self.build_log_size = None
        self.build_time = 0
        self.build_type = None
        self.compiler = None
        self.compiler_version = None
        self.compiler_version_ext = None
        self.compiler_version_full = None
        self.build_environment = build_environment
        self.cross_compile = None
        self.dirname = None
        self.dtb_dir = None
        self.dtb_dir_data = []
        self.errors = 0
        self.file_server_resource = None
        self.file_server_url = None
        self.git_commit = None
        self.git_describe = None
        self.git_describe_v = None
        self.git_url = None
        self.job_id = None
        self.kconfig_fragments = None
        self.kernel_config = None
        self.kernel_config_size = None
        self.kernel_image = None
        self.kernel_image_size = None
        self.kernel_version = None
        self.modules = None
        self.modules_dir = None
        self.modules_size = None
        self.system_map = None
        self.system_map_size = None
        self.text_offset = None
        self.vmlinux_bss_size = None
        self.vmlinux_data_size = None
        self.vmlinux_file_size = None
        self.vmlinux_text_size = None
        self.warnings = 0

    @property
    def collection(self):
        return models.BUILD_COLLECTION

    @property
    def created_on(self):
        """When this object was created."""
        return self._created_on

    @created_on.setter
    def created_on(self, value):
        """Set the creation date of this object.

        :param value: The document creation date, in UTC time zone.
        :type value: datetime
        """
        self._created_on = value

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
    def version(self):
        """The schema version of this object."""
        return self._version

    @version.setter
    def version(self, value):
        """Set the schema version of this object.

        :param value: The schema string.
        :type param: str
        """
        self._version = value

    @property
    def metadata(self):
        """A dictionary with metadata about this build."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set the metadata about this build.

        :param value: A dictionary with build metadata.
        """
        if not isinstance(value, types.DictionaryType):
            raise TypeError(
                "Passed value is not a dictionary, got %s", type(value)
            )
        self._metadata = value

    @property
    def status(self):
        """The status of this build."""
        return self._status

    @status.setter
    def status(self, value):
        """Set the status.

        :param value: The status as string.
        """
        if value not in models.VALID_BUILD_STATUS:
            raise ValueError(
                "Status value '%s' not valid, should be one of: %s",
                value, str(models.VALID_BUILD_STATUS)
            )
        self._status = value

    @property
    def build_platform(self):
        """Details about the platform used to build."""
        return self._build_platform

    @build_platform.setter
    def build_platform(self, value):
        """Set details about the build platform."""
        if not isinstance(value, types.ListType):
            raise TypeError("Value passed is not a list: %s", type(value))
        self._build_platform = value

    def to_dict(self):
        defconf_dict = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BUILD_LOG_KEY: self.build_log,
            models.BUILD_LOG_SIZE_KEY: self.build_log_size,
            models.BUILD_PLATFORM_KEY: self.build_platform,
            models.BUILD_TIME_KEY: self.build_time,
            models.BUILD_TYPE_KEY: self.build_type,
            models.COMPILER_KEY: self.compiler,
            models.COMPILER_VERSION_EXT_KEY: self.compiler_version_ext,
            models.COMPILER_VERSION_FULL_KEY: self.compiler_version_full,
            models.COMPILER_VERSION_KEY: self.compiler_version,
            models.BUILD_ENVIRONMENT_KEY: self.build_environment,
            models.CREATED_KEY: self.created_on,
            models.CROSS_COMPILE_KEY: self.cross_compile,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DIRNAME_KEY: self.dirname,
            models.DTB_DIR_DATA_KEY: self.dtb_dir_data,
            models.DTB_DIR_KEY: self.dtb_dir,
            models.ERRORS_KEY: self.errors,
            models.FILE_SERVER_RESOURCE_KEY: self.file_server_resource,
            models.FILE_SERVER_URL_KEY: self.file_server_url,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_DESCRIBE_V_KEY: self.git_describe_v,
            models.GIT_URL_KEY: self.git_url,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KCONFIG_FRAGMENTS_KEY: self.kconfig_fragments,
            models.KERNEL_CONFIG_KEY: self.kernel_config,
            models.KERNEL_CONFIG_SIZE_KEY: self.kernel_config_size,
            models.KERNEL_IMAGE_KEY: self.kernel_image,
            models.KERNEL_IMAGE_SIZE_KEY: self.kernel_image_size,
            models.KERNEL_KEY: self.kernel,
            models.KERNEL_VERSION_KEY: self.kernel_version,
            models.METADATA_KEY: self.metadata,
            models.MODULES_DIR_KEY: self.modules_dir,
            models.MODULES_KEY: self.modules,
            models.MODULES_SIZE_KEY: self.modules_size,
            models.STATUS_KEY: self.status,
            models.SYSTEM_MAP_KEY: self.system_map,
            models.SYSTEM_MAP_SIZE_KEY: self.system_map_size,
            models.TEXT_OFFSET_KEY: self.text_offset,
            models.VERSION_KEY: self.version,
            models.VMLINUX_BSS_SIZE_KEY: self.vmlinux_bss_size,
            models.VMLINUX_DATA_SIZE_KEY: self.vmlinux_data_size,
            models.VMLINUX_FILE_SIZE_KEY: self.vmlinux_file_size,
            models.VMLINUX_TEXT_SIZE_KEY: self.vmlinux_text_size,
            models.WARNINGS_KEY: self.warnings
        }

        if self.id:
            defconf_dict[models.ID_KEY] = self.id

        return defconf_dict

    @staticmethod
    def from_json(json_obj):
        build_doc = None
        if all([json_obj, isinstance(json_obj, types.DictionaryType)]):
            local_obj = copy.deepcopy(json_obj)
            doc_pop = local_obj.pop

            doc_id = doc_pop(models.ID_KEY, None)
            defconfig_full = doc_pop(models.DEFCONFIG_FULL_KEY, None)
            doc_pop(models.NAME_KEY, None)
            try:
                job = doc_pop(models.JOB_KEY)
                kernel = doc_pop(models.KERNEL_KEY)
                defconfig = doc_pop(models.DEFCONFIG_KEY)
                git_branch = doc_pop(models.GIT_BRANCH_KEY)
                build_environment = doc_pop(models.BUILD_ENVIRONMENT_KEY)

                build_doc = BuildDocument(
                    job,
                    kernel,
                    defconfig, git_branch, build_environment,
                    defconfig_full=defconfig_full)
                build_doc.id = doc_id

                for key, val in local_obj.iteritems():
                    setattr(build_doc, key, val)
            except KeyError:
                # Missing mandatory key? Return None.
                build_doc = None
        return build_doc
