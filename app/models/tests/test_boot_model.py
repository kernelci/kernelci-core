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
        self.maxDiff = None
        boot_doc = modbt.BootDocument(
            'board', 'job', 'kernel', 'defconfig', 'lab'
        )
        boot_doc.id = 'id'
        boot_doc.job_id = 'job-id'
        boot_doc.created_on = 'now'
        boot_doc.defconfig_id = "defconfig_id"
        boot_doc.retries = 10
        boot_doc.version = "1.0"
        boot_doc.dtb_append = False
        boot_doc.boot_log = "boot-log"
        boot_doc.boot_log_html = "boot-log-html"

        expected = {
            '_id': 'id',
            'board': 'board',
            'boot_log': "boot-log",
            'boot_log_html': "boot-log-html",
            'boot_result_description': None,
            'created_on': 'now',
            'defconfig': 'defconfig',
            'defconfig_id': "defconfig_id",
            'dtb': None,
            'dtb_addr': None,
            'dtb_append': False,
            'endian': None,
            'fastboot': None,
            'initrd_addr': None,
            'job': 'job',
            'job_id': 'job-id',
            'kernel': 'kernel',
            'kernel_image': None,
            'lab_name': 'lab',
            'load_addr': None,
            'metadata': {},
            'name': 'board-job-kernel-defconfig',
            'retries': 10,
            'status': None,
            'time': None,
            'version': "1.0",
            'warnings': None,
        }

        self.assertDictEqual(expected, boot_doc.to_dict())
