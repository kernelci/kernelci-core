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

from base import BaseDocument

DEFCONFIG_COLLECTION = 'defconfig'
DEFCONFIG_ACCEPTED_FILES = {
    'zImage': 'zimage',
    'Image': 'image',
    'System.map': 'system_map',
    'kernel.config': 'kernel_conf',
}


class DefConfigDocument(BaseDocument):

    def __init__(self, name, job_id=None):
        super(DefConfigDocument, self).__init__(name)

        self._job_id = job_id
        self._zimage = None
        self._image = None
        self._system_map = None
        self._kernel_conf = None

    @property
    def collection(self):
        return DEFCONFIG_COLLECTION

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        self._job_id = value

    @property
    def zimage(self):
        return self._zimage

    @zimage.setter
    def zimage(self, value):
        self._zimage = value

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    @property
    def system_map(self):
        return self._system_map

    @system_map.setter
    def system_map(self, value):
        self._system_map = value

    @property
    def kernel_conf(self):
        return self._kernel_conf

    @kernel_conf.setter
    def kernel_conf(self, value):
        self._kernel_conf = value

    def to_dict(self):
        defconf_dict = super(DefConfigDocument, self).to_dict()
        defconf_dict['job_id'] = self._job_id
        defconf_dict['zimage'] = self._zimage
        defconf_dict['image'] = self._image
        defconf_dict['system_map'] = self._system_map
        defconf_dict['kernel_conf'] = self._kernel_conf
        return defconf_dict
