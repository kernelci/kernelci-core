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
import models.error_summary as msumm


class TestErrorSummaryModel(unittest.TestCase):

    def test_doc_valid_instance(self):
        doc = msumm.ErrorSummaryDocument("job_id", "1.1")
        self.assertIsInstance(doc, modb.BaseDocument)
        self.assertIsInstance(doc, msumm.ErrorSummaryDocument)

    def test_doc_collection(self):
        doc = msumm.ErrorSummaryDocument("job_id", "1.1")
        self.assertEqual("errors_summary", doc.collection)

    def test_doc_wrong_lists(self):
        doc = msumm.ErrorSummaryDocument("job_id", "1.1")

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
        doc = msumm.ErrorSummaryDocument("job_id", "1.1")
        doc.git_branch = "branch"
        doc.errors = [("error1", 1)]
        doc.job = "job"
        doc.kernel = "kernel"
        doc.mismatches = [("mismatch1", 1)]
        doc.warnings = [("warning1", 1)]
        doc.created_on = "today"
        doc.version = "1.1"

        expected = {
            "created_on": "today",
            "errors": [("error1", 1)],
            "git_branch": "branch",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "mismatches": [("mismatch1", 1)],
            "version": "1.1",
            "warnings": [("warning1", 1)]
        }

        self.assertDictEqual(expected, doc.to_dict())

        doc.id = "id"
        expected["_id"] = "id"
        self.assertDictEqual(expected, doc.to_dict())

    def test_doc_from_json(self):
        json_obj = {
            "_id": "id",
            "created_on": "today",
            "errors": [("error1", 1)],
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "mismatches": [("mismatch1", 1)],
            "name": "job_id",
            "version": "1.1",
            "warnings": [("warning1", 1)]
        }

        self.assertIsNone(msumm.ErrorSummaryDocument.from_json(json_obj))
