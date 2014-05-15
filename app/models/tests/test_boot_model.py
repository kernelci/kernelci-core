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

import unittest

from models.base import BaseDocument
from models.boot import BootDocument


class TestBootModel(unittest.TestCase):

    def test_boot_document_valid_instance(self):
        boot_doc = BootDocument('board', 'job', 'kernel', 'defconfig')
        self.assertIsInstance(boot_doc, BaseDocument)

    def test_boot_document_to_dict(self):
        boot_doc = BootDocument('board', 'job', 'kernel', 'defconfig')

        expected = {
            'status': None,
            'time': None,
            'warnings': None,
            'kernel': 'kernel',
            'job_id': 'job-kernel',
            'created_on': None,
            'fail_log': [],
            'defconfig': 'defconfig',
            'job': 'job',
            '_id': 'board-job-kernel-defconfig',
            'board': 'board',
        }

        self.assertEqual(expected, boot_doc.to_dict())

    def test_boot_document_to_json(self):
        boot_doc = BootDocument('board', 'job', 'kernel', 'defconfig')

        expected = (
            '{"status": null, "kernel": "kernel", "job_id": "job-kernel", '
            '"warnings": null, "fail_log": [], "created_on": null, '
            '"defconfig": "defconfig", "job": "job", "board": "board", '
            '"time": null, "_id": "board-job-kernel-defconfig"}'
        )

        self.assertEqual(expected, boot_doc.to_json())
