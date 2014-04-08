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

from models.base import BaseDocument

DEFCONFIG_COLLECTION = 'defconfig'
# Mapping used during the import phase.
DEFCONFIG_ACCEPTED_FILES = {
    'zImage': 'zimage',
    'Image': 'image',
    'System.map': 'system_map',
    'kernel.config': 'kernel_conf',
    'build.log': 'build_log',
}


class DefConfigDocument(BaseDocument):
    """This class represents a defconfig folder as seen on the file system."""

    DEFCONFIG_ID_FORMAT = '%s-%s'

    def __init__(self, name, job_id):
        super(DefConfigDocument, self).__init__(
            self.DEFCONFIG_ID_FORMAT % (job_id, name)
        )

        self._job_id = job_id
        self._zimage = None
        self._image = None
        self._system_map = None
        self._kernel_conf = None
        self._status = None
        self._build_log = None

    @property
    def collection(self):
        return DEFCONFIG_COLLECTION

    @property
    def job_id(self):
        """The job ID this defconfig belogns to."""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        """Set the job ID this defconfig belongs to."""
        self._job_id = value

    @property
    def zimage(self):
        """The path to the zImage file produced by this defconfig.

        :return None if there is no zImage file, or its path.
        """
        return self._zimage

    @zimage.setter
    def zimage(self, value):
        """Set the zImage path."""
        self._zimage = value

    @property
    def image(self):
        """The path to the Image file produced by this defconfig.

        :return None if there is no Image file, or its path.
        """
        return self._image

    @image.setter
    def image(self, value):
        """Set the Image path."""
        self._image = value

    @property
    def system_map(self):
        """The path to the System.map file produced by this defconfig.

        :return None if there is not System.map file, or its path.
        """
        return self._system_map

    @system_map.setter
    def system_map(self, value):
        """Set the System.map path"""
        self._system_map = value

    @property
    def kernel_conf(self):
        """The path to kernel.config produced by this defconfig.

        :return None if there is no kernel.config file, or its path.
        """
        return self._kernel_conf

    @kernel_conf.setter
    def kernel_conf(self, value):
        """Set the kernel.config path."""
        self._kernel_conf = value

    @property
    def build_log(self):
        """The path to the `build.log` file.

        :return None if there is no `build.log` file, or its path.
        """
        return self._build_log

    @build_log.setter
    def build_log(self, value):
        """Set the build.log path."""
        self._build_log = value

    def to_dict(self):
        defconf_dict = super(DefConfigDocument, self).to_dict()
        defconf_dict['job_id'] = self._job_id
        defconf_dict['zimage'] = self._zimage
        defconf_dict['image'] = self._image
        defconf_dict['system_map'] = self._system_map
        defconf_dict['kernel_conf'] = self._kernel_conf
        defconf_dict['build_log'] = self._build_log
        defconf_dict['status'] = self._status
        return defconf_dict
