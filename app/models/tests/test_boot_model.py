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

import unittest

import models.base as modb
import models.boot as modbt


class TestBootModel(unittest.TestCase):

    def test_boot_document_valid_instance(self):
        boot_doc = modbt.BootDocument(
            'board', 'job', 'kernel', 'defconfig', 'lab'
        )
        self.assertIsInstance(boot_doc, modb.BaseDocument)

    def test_boot_document_to_dict(self):
        boot_doc = modbt.BootDocument(
            'board', 'job', 'kernel', 'defconfig', 'lab'
        )
        boot_doc.id = 'id'
        boot_doc.job_id = 'job-id'
        boot_doc.created_on = 'now'

        expected = {
            'name': 'board-job-kernel-defconfig',
            'kernel': 'kernel',
            'defconfig': 'defconfig',
            'board': 'board',
            'job_id': 'job-id',
            'job': 'job',
            '_id': 'id',
            'lab_id': 'lab',
            'created_on': 'now',
            'status': None,
            'time': None,
            'warnings': None,
            'load_addr': None,
            'dtb': None,
            'dtb_addr': None,
            'initrd_addr': None,
            'kernel_image': None,
            'boot_log': None,
            'endian': None,
            'metadata': {},
            'boot_log_html': None,
            'fastboot': None,
            'retries': None,
            'boot_result_description': None,
        }

        self.assertDictEqual(expected, boot_doc.to_dict())
