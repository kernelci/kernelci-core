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
import models.error_log as merrl


class TestErrorLogModel(unittest.TestCase):

    def test_doc_valid_instance(self):
        doc = merrl.ErrorLogDocument("job_id", "1.1")
        self.assertIsInstance(doc, modb.BaseDocument)
        self.assertIsInstance(doc, merrl.ErrorLogDocument)

    def test_doc_collection(self):
        doc = merrl.ErrorLogDocument("job_id", "1.1")
        self.assertEqual("error_logs", doc.collection)

    def test_doc_wrong_lists(self):
        doc = merrl.ErrorLogDocument("job_id", "1.1")

        self.assertRaises(TypeError, setattr, doc, "errors", {})
        self.assertRaises(TypeError, setattr, doc, "errors", "")
        self.assertRaises(TypeError, setattr, doc, "errors", 0)
        self.assertRaises(TypeError, setattr, doc, "errors", ())

        self.assertRaises(TypeError, setattr, doc, "warnings", {})
        self.assertRaises(TypeError, setattr, doc, "warnings", "")
        self.assertRaises(TypeError, setattr, doc, "warnings", 0)
        self.assertRaises(TypeError, setattr, doc, "warnings", ())

        self.assertRaises(TypeError, setattr, doc, "mismatches", {})
        self.assertRaises(TypeError, setattr, doc, "mismatches", "")
        self.assertRaises(TypeError, setattr, doc, "mismatches", 0)
        self.assertRaises(TypeError, setattr, doc, "mismatches", ())

    def test_doc_to_dict(self):
        doc = merrl.ErrorLogDocument("job_id", "1.1")
        doc.arch = "arm"
        doc.created_on = "today"
        doc.defconfig = "defconfig"
        doc.defconfig_full = "defconfig_full"
        doc.build_id = "build-id"
        doc.errors = ["error1"]
        doc.errors_count = 1
        doc.job = "job"
        doc.kernel = "kernel"
        doc.mismatches = ["mismatch1"]
        doc.mismatches_count = 1
        doc.status = "FAIL"
        doc.warnings = ["warning1"]
        doc.warnings_count = 1
        doc.file_server_url = "foo"
        doc.file_server_resource = "bar"
        doc.compiler = "gcc"
        doc.compiler_version = "gcc version"
        doc.compiler_version_ext = "gcc version ext"
        doc.compiler_version_full = "gcc version full"
        doc.git_branch = "branch"
        doc.build_environment = "build_environment"

        expected = {
            "arch": "arm",
            "created_on": "today",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "build_id": "build-id",
            "errors": ["error1"],
            "errors_count": 1,
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "mismatches": ["mismatch1"],
            "mismatches_count": 1,
            "status": "FAIL",
            "version": "1.1",
            "warnings": ["warning1"],
            "warnings_count": 1,
            "file_server_url": "foo",
            "file_server_resource": "bar",
            "compiler": "gcc",
            "compiler_version": "gcc version",
            "compiler_version_ext": "gcc version ext",
            "compiler_version_full": "gcc version full",
            "git_branch": "branch",
            "build_environment": "build_environment"
        }

        self.assertDictEqual(expected, doc.to_dict())

        doc.id = "id"
        expected["_id"] = "id"
        self.assertDictEqual(expected, doc.to_dict())

    def test_doc_from_json(self):
        json_obj = {
            "_id": "id",
            "arch": "arm",
            "created_on": "today",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "build_id": "build-id",
            "errors": ["error1"],
            "errors_count": 1,
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "mismatches": ["mismatch1"],
            "mismatches_count": 1,
            "name": "job_id",
            "status": "FAIL",
            "version": "1.0",
            "warnings": ["warning1"],
            "warnings_count": 1
        }

        self.assertIsNone(merrl.ErrorLogDocument.from_json(json_obj))
