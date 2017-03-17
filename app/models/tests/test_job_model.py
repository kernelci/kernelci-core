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
        job_doc = modj.JobDocument("job", "kernel", "git-branch")
        self.assertIsInstance(job_doc, modb.BaseDocument)
        self.assertIsInstance(job_doc, modj.JobDocument)

    def test_job_correct_status(self):
        job_doc = modj.JobDocument("job", "kernel", "git-branch")

        job_doc.status = "FAIL"
        self.assertEqual(job_doc.status, "FAIL")
        job_doc.status = "BUILD"
        self.assertEqual(job_doc.status, "BUILD")
        job_doc.status = "PASS"
        self.assertEqual(job_doc.status, "PASS")

    def test_job_document_to_dict(self):
        job_doc = modj.JobDocument("job", "kernel", "git-branch")
        job_doc.id = "job"
        job_doc.created_on = "now"
        job_doc.status = "PASS"
        job_doc.git_commit = "1234"
        job_doc.git_url = "git-url"
        job_doc.git_describe = "git-describe"
        job_doc.git_describe_v = "git-describe-v"
        job_doc.kernel_version = "kernel-version"
        job_doc.compiler = "gcc"
        job_doc.compiler_version = "4.7.3"
        job_doc.compiler_version_ext = "gcc 4.7.3"
        job_doc.compiler_version_full = "gcc version 4.7.3"
        job_doc.cross_compile = "cross-compile"

        expected = {
            "_id": "job",
            "kernel": "kernel",
            "job": "job",
            "private": False,
            "created_on": "now",
            "status": "PASS",
            "version": "1.1",
            "git_commit": "1234",
            "git_url": "git-url",
            "git_branch": "git-branch",
            "git_describe": "git-describe",
            "git_describe_v": "git-describe-v",
            "kernel_version": "kernel-version",
            "compiler": "gcc",
            "compiler_version": "4.7.3",
            "compiler_version_ext": "gcc 4.7.3",
            "compiler_version_full": "gcc version 4.7.3",
            "cross_compile": "cross-compile"
        }

        self.assertEqual(job_doc.to_dict(), expected)

    def test_job_document_collection(self):
        job_doc = modj.JobDocument("job", "kernel", "git-branch")
        self.assertEqual(job_doc.collection, "job")

    def test_job_document_from_json(self):
        now = datetime.datetime.now(tz=tz_util.utc)

        json_obj = dict(
            _id="job",
            job="job",
            kernel="kernel",
            git_branch="git-branch",
            created_on=now,
            status="BUILD"
        )

        job_doc = modj.JobDocument.from_json(json_obj)

        self.assertIsInstance(job_doc, modj.JobDocument)
        self.assertIsInstance(job_doc, modb.BaseDocument)
        self.assertEqual(job_doc.kernel, "kernel")
        self.assertEqual(job_doc.job, "job")
        self.assertEqual(job_doc.created_on, now)
        self.assertEqual(job_doc.status, "BUILD")
        self.assertEqual(job_doc.git_branch, "git-branch")
        self.assertEqual(job_doc.version, "1.1")

    def test_job_document_private(self):
        # By default, jobs are public.
        job_doc = modj.JobDocument("job", "kernel", "git-branch")

        self.assertFalse(job_doc.private)

        job_doc.private = True

        self.assertTrue(job_doc.private)

    def test_job_document_date_serialization(self):
        now = datetime.datetime.now(tz=tz_util.utc)

        job_doc = modj.JobDocument("job", "kernel", "git-branch")
        job_doc.created_on = now

        self.assertIsInstance(job_doc.created_on, datetime.datetime)

        json_obj = {
            "_id": "job",
            "job": "job",
            "kernel": "kernel",
            "git_branch": "git-branch",
            "created_on": now
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
