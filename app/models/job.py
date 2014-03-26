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

JOB_COLLECTION = 'job'


class JobDocument(BaseDocument):

    JOB_ID_FORMAT = '%s-%s'

    def __init__(self, name, job=None, kernel=None):
        super(JobDocument, self).__init__(name)

        self._private = False
        self._job = job
        self._kernel = kernel
        self._created = None

    @property
    def collection(self):
        return JOB_COLLECTION

    @property
    def private(self):
        return self._private

    @private.setter
    def private(self, value):
        self._private = value

    @property
    def job(self):
        return self._job

    @job.setter
    def job(self, value):
        self._job = value

    @property
    def kernel(self):
        return self._kernel

    @kernel.setter
    def kernel(self, value):
        self._kernel = value

    @property
    def created(self):
        return self._created

    @created.setter
    def created(self, value):
        self._created = value

    def to_dict(self):
        job_dict = super(JobDocument, self).to_dict()
        job_dict['private'] = self._private
        job_dict['job'] = self._job
        job_dict['kernel'] = self._kernel
        job_dict['created'] = str(self._created)
        return job_dict
