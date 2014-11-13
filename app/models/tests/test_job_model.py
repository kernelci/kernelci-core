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

import datetime
import unittest

from bson import (
    json_util,
    tz_util,
)

import models.base as modb
import models.job as modj


class TestJobModel(unittest.TestCase):

    def test_job_documet_valid_instance(self):
        job_doc = modj.JobDocument("job", "kernel")
        self.assertIsInstance(job_doc, modb.BaseDocument)
        self.assertIsInstance(job_doc, modj.JobDocument)

    def test_job_wrong_status(self):
        job_doc = modj.JobDocument("job", "kernel")

        self.assertRaises(ValueError, setattr, job_doc, "status", "foo")
        self.assertRaises(ValueError, setattr, job_doc, "status", [])
        self.assertRaises(ValueError, setattr, job_doc, "status", ())
        self.assertRaises(ValueError, setattr, job_doc, "status", {})

    def test_job_correct_status(self):
        job_doc = modj.JobDocument("job", "kernel")

        job_doc.status = "FAIL"
        self.assertEqual(job_doc.status, "FAIL")
        job_doc.status = "BUILD"
        self.assertEqual(job_doc.status, "BUILD")
        job_doc.status = "PASS"
        self.assertEqual(job_doc.status, "PASS")

    def test_job_document_to_dict(self):
        job_doc = modj.JobDocument("job", "kernel")
        job_doc.id = "job"
        job_doc.created_on = "now"
        job_doc.status = "PASS"
        job_doc.version = "1.0"

        expected = {
            "_id": "job",
            "name": "job-kernel",
            "kernel": "kernel",
            "job": "job",
            "private": False,
            "created_on": "now",
            "status": "PASS",
            "version": "1.0",
        }

        self.assertEqual(job_doc.to_dict(), expected)

    def test_job_document_collection(self):
        job_doc = modj.JobDocument("job", "kernel")
        self.assertEqual(job_doc.collection, "job")

    def test_job_document_from_json(self):
        now = datetime.datetime.now(tz=tz_util.utc)

        json_obj = dict(
            _id="job",
            job="job",
            kernel="kernel",
            created_on=now,
            status="BUILD",
            name="job-kernel"
        )

        job_doc = modj.JobDocument.from_json(json_obj)

        self.assertIsInstance(job_doc, modj.JobDocument)
        self.assertIsInstance(job_doc, modb.BaseDocument)
        self.assertEqual(job_doc.name, 'job-kernel')
        self.assertEqual(job_doc.kernel, 'kernel')
        self.assertEqual(job_doc.job, 'job')
        self.assertEqual(job_doc.created_on, now)
        self.assertEqual(job_doc.status, 'BUILD')

    def test_job_document_private(self):
        # By default, jobs are public.
        job_doc = modj.JobDocument("job", "kernel")

        self.assertFalse(job_doc.private)

        job_doc.private = True

        self.assertTrue(job_doc.private)

    def test_job_document_date_serialization(self):
        now = datetime.datetime.now(tz=tz_util.utc)

        job_doc = modj.JobDocument("job", "kernel")
        job_doc.created_on = now

        self.assertIsInstance(job_doc.created_on, datetime.datetime)

        json_obj = {
            "_id": "job",
            "job": "job",
            "kernel": "kernel",
            "name": "job-kernel",
            "created_on": now,
        }

        json_deserialized = json_util.loads(json_util.dumps(json_obj))
        new_job = modj.JobDocument.from_json(json_deserialized)

        self.assertIsInstance(new_job.created_on, datetime.datetime)
        # During the deserialization process, some microseconds are lost.
        self.assertLessEqual(
            (new_job.created_on - job_doc.created_on).total_seconds(), 0)

    def test_job_document_from_wrong_json(self):
        self.assertIsNone(modj.JobDocument.from_json(None))
        self.assertIsNone(modj.JobDocument.from_json({}))
        self.assertIsNone(modj.JobDocument.from_json([]))
        self.assertIsNone(modj.JobDocument.from_json(""))
        self.assertIsNone(modj.JobDocument.from_json(()))
