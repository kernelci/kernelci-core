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

"""The model that represents a defconfing document in the db."""

import types

import models
import models.base as modb


# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
class DefconfigDocument(modb.BaseDocument):

    """This class represents a defconfig folder as seen on the file system."""

    def __init__(self, job, kernel, defconfig, defconfig_full=None):

        doc_name = {
            models.JOB_KEY: job,
            models.KERNEL_KEY: kernel,
            models.DEFCONFIG_KEY: defconfig_full or defconfig
        }

        self._created_on = None
        self._id = None
        self._name = models.DEFCONFIG_DOCUMENT_NAME % doc_name
        self._version = None

        self._build_platform = []
        self._defconfig = defconfig
        self._defconfig_full = defconfig_full or defconfig
        self._job = job
        self._kernel = kernel
        self._metadata = {}
        self._status = None
        self.arch = None
        self.build_log = None
        self.build_time = 0
        self.dirname = None
        self.dtb_dir = None
        self.errors = 0
        self.file_server_resource = None
        self.file_server_url = None
        self.git_branch = None
        self.git_commit = None
        self.git_describe = None
        self.git_url = None
        self.job_id = None
        self.kconfig_fragments = None
        self.kernel_config = None
        self.kernel_image = None
        self.modules = None
        self.modules_dir = None
        self.system_map = None
        self.text_offset = None
        self.warnings = 0

    @property
    def collection(self):
        return models.DEFCONFIG_COLLECTION

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
    def name(self):
        """The name of the object."""
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
    def job(self):
        """The job this defconfig belongs too."""
        return self._job

    @property
    def kernel(self):
        """The kernel this defconfig was built against."""
        return self._kernel

    @property
    def defconfig(self):
        """The defconfig name."""
        return self._defconfig

    @property
    def metadata(self):
        """A dictionary with metadata about this defconfig."""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set the metadata about this defconfig.

        :param value: A dictionary with defconfig metadata.
        """
        if not isinstance(value, types.DictionaryType):
            raise TypeError(
                "Passed value is not a dictionary, got %s", type(value)
            )
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
    def defconfig_full(self):
        """The full defconfig name.

        This parameter contains also the config fragments information.
        """
        return self._defconfig_full

    @defconfig_full.setter
    def defconfig_full(self, value):
        """Set the full defconfig name."""
        self._defconfig_full = value

    def to_dict(self):
        defconf_dict = {
            models.ARCHITECTURE_KEY: self.arch,
            models.BUILD_LOG_KEY: self.build_log,
            models.BUILD_PLATFORM_KEY: self.build_platform,
            models.BUILD_TIME_KEY: self.build_time,
            models.CREATED_KEY: self.created_on,
            models.DEFCONFIG_FULL_KEY: self.defconfig_full,
            models.DEFCONFIG_KEY: self.defconfig,
            models.DIRNAME_KEY: self.dirname,
            models.DTB_DIR_KEY: self.dtb_dir,
            models.ERRORS_KEY: self.errors,
            models.FILE_SERVER_RESOURCE_KEY: self.file_server_resource,
            models.FILE_SERVER_URL_KEY: self.file_server_url,
            models.GIT_BRANCH_KEY: self.git_branch,
            models.GIT_COMMIT_KEY: self.git_commit,
            models.GIT_DESCRIBE_KEY: self.git_describe,
            models.GIT_URL_KEY: self.git_url,
            models.JOB_ID_KEY: self.job_id,
            models.JOB_KEY: self.job,
            models.KCONFIG_FRAGMENTS_KEY: self.kconfig_fragments,
            models.KERNEL_CONFIG_KEY: self.kernel_config,
            models.KERNEL_IMAGE_KEY: self.kernel_image,
            models.KERNEL_KEY: self.kernel,
            models.METADATA_KEY: self.metadata,
            models.MODULES_DIR_KEY: self.modules_dir,
            models.MODULES_KEY: self.modules,
            models.NAME_KEY: self.name,
            models.STATUS_KEY: self.status,
            models.SYSTEM_MAP_KEY: self.system_map,
            models.TEXT_OFFSET_KEY: self.text_offset,
            models.VERSION_KEY: self.version,
            models.WARNINGS_KEY: self.warnings,
        }

        if self.id:
            defconf_dict[models.ID_KEY] = self.id

        return defconf_dict

    @staticmethod
    def from_json(json_obj):
        return None
