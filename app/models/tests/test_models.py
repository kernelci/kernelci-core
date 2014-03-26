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

from models import (
    BaseDocument,
    DefConfigDocument,
    JobDocument,
)


class TestModels(unittest.TestCase):

    def test_job_documet_valid_instance(self):
        job_doc = JobDocument('job')
        self.assertIsInstance(job_doc, BaseDocument)

    def test_job_document_to_dict(self):
        expected = {
            'kernel': None,
            'job': None,
            '_id': 'job',
            'private': False,
            'created': 'None'
        }
        job_doc = JobDocument('job')
        self.assertEqual(job_doc.to_dict(), expected)

    def test_job_document_collection(self):
        job_doc = JobDocument('job')
        self.assertEqual(job_doc.collection, 'job')

    def test_job_document_to_json(self):
        expected_json = (
            '{"kernel": null, "job": null, "_id": "job", "private": false, '
            '"created": "None"}'
        )

        job_doc = JobDocument('job')
        self.assertEqual(job_doc.to_json(), expected_json)

    def test_defconfig_document_valid_instance(self):
        defconf_doc = DefConfigDocument('defconf')
        self.assertIsInstance(defconf_doc, BaseDocument)

    def test_defconfig_document_to_dict(self):
        expected = {
            'job_id': None,
            'image': None,
            'system_map': None,
            'zimage': None,
            '_id': 'defconfig',
            'job_id': None,
            'kernel_conf': None,
        }

        defconfig_doc = DefConfigDocument('defconfig')
        self.assertEqual(defconfig_doc.to_dict(), expected)

    def test_defconfig_document_collection(self):
        defconfig_doc = DefConfigDocument('defconfig')
        self.assertEqual(defconfig_doc.collection, 'defconfig')

    def test_defconfig_document_to_json(self):
        expected_json = (
            '{"job_id": null, "image": null, "system_map": null, '
            '"zimage": null, "_id": "defconfig", "kernel_conf": null}'
        )

        defconfig_doc = DefConfigDocument('defconfig')
        self.assertEqual(defconfig_doc.to_json(), expected_json)

    def test_defconfig_document_kernel_setter(self):
        expected_json = (
            '{"job_id": "job", "image": null, "system_map": null, '
            '"zimage": null, "_id": "defconfig", "kernel_conf": null}'
        )

        defconf_doc = DefConfigDocument('defconfig')
        defconf_doc.job_id = "job"

        self.assertEqual(defconf_doc.job_id, 'job')
        self.assertEqual(defconf_doc.to_json(), expected_json)
