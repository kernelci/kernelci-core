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

import json
import types
import unittest

from models.base import BaseDocument
from models.defconfig import DefConfigDocument
from models.job import JobDocument
from models.subscription import SubscriptionDocument


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
        defconf_doc = DefConfigDocument('defconf', 'job')
        self.assertIsInstance(defconf_doc, BaseDocument)

    def test_defconfig_document_to_dict(self):
        expected = {
            'job_id': 'job',
            'image': None,
            'system_map': None,
            'zimage': None,
            '_id': 'job-defconfig',
            'kernel_conf': None,
        }

        defconfig_doc = DefConfigDocument('defconfig', 'job')
        self.assertEqual(defconfig_doc.to_dict(), expected)

    def test_defconfig_document_collection(self):
        defconfig_doc = DefConfigDocument('defconfig', 'job')
        self.assertEqual(defconfig_doc.collection, 'defconfig')

    def test_defconfig_document_to_json(self):
        expected_json = (
            '{"job_id": "job", "image": null, "system_map": null, '
            '"zimage": null, "_id": "job-defconfig", "kernel_conf": null}'
        )

        defconfig_doc = DefConfigDocument('defconfig', 'job')
        self.assertEqual(defconfig_doc.to_json(), expected_json)

    def test_subscription_document_emails_attribute(self):
        subscription_doc = SubscriptionDocument('sub', 'job')
        self.assertIsInstance(subscription_doc.emails, types.ListType)
        self.assertItemsEqual([], subscription_doc.emails)

    def test_subscription_document_emails_attribute_set(self):
        subscription_doc = SubscriptionDocument('sub', 'job', 'email')

        self.assertIsInstance(subscription_doc.emails, types.ListType)
        self.assertNotIsInstance(subscription_doc.emails, types.StringTypes)

    def test_subscription_document_emails_extended(self):
        subscription_doc = SubscriptionDocument('sub', 'job', 'email')
        subscription_doc.emails = 'email2'

        self.assertIsInstance(subscription_doc.emails, types.ListType)
        self.assertEquals(['email2', 'email'], subscription_doc.emails)

    def test_subscription_document_emails_setter_str(self):
        subscription_doc = SubscriptionDocument('sub', 'job')
        subscription_doc.emails = 'an_email'

        self.assertIsInstance(subscription_doc.emails, types.ListType)
        self.assertEqual(['an_email'], subscription_doc.emails)

    def test_subscription_document_to_dict(self):
        expected = dict(_id='sub', emails=[], job_id='job')
        subscription_doc = SubscriptionDocument('sub', 'job')

        self.assertEqual(expected, subscription_doc.to_dict())

    def test_subscription_document_to_json(self):
        expected = (
            '{"_id": "sub", "emails": [], "job_id": "job"}'
        )
        subscription_doc = SubscriptionDocument('sub', 'job')
        self.assertEqual(expected, subscription_doc.to_json())

    def test_subscription_document_from_json(self):
        json_str = (
            '{"_id": "sub", "emails": [], "job_id": "job"}'
        )
        json_obj = json.loads(json_str)

        subscription_doc = SubscriptionDocument.from_json(json_obj)

        self.assertIsInstance(subscription_doc, SubscriptionDocument)
        self.assertIsInstance(subscription_doc, BaseDocument)
