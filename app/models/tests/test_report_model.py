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

import models.base as mbase
import models.report as mreport


class TestReportModel(unittest.TestCase):

    def test_report_document_valid_instance(self):
        report_doc = mreport.ReportDocument("name")
        self.assertIsInstance(report_doc, mbase.BaseDocument)

    def test_report_document_to_dict(self):
        self.maxDiff = None
        report_doc = mreport.ReportDocument("name")
        report_doc.id = "id"
        report_doc.created_on = "now"
        report_doc.job = "job"
        report_doc.kernel = "kernel"
        report_doc.report_type = "boot"
        report_doc.status = "ERROR"
        report_doc.updated_on = "now"
        report_doc.errors = [(1, "msg")]

        expected = {
            "_id": "id",
            "created_on": "now",
            "errors": [(1, "msg")],
            "job": "job",
            "kernel": "kernel",
            "name": "name",
            "status": "ERROR",
            "type": "boot",
            "updated_on": "now",
            "version": "1.0"
        }

        self.assertDictEqual(expected, report_doc.to_dict())

    def test_report_document_from_json(self):
        json_obj = {
            "_id": "id",
            "created_on": "now",
            "job": "job",
            "kernel": "kernel",
            "name": "name",
            "type": "build",
            "version": "1.1"
        }
        report_doc = mreport.ReportDocument.from_json(json_obj)

        self.assertIsInstance(report_doc, mbase.BaseDocument)
        self.assertIsInstance(report_doc, mreport.ReportDocument)

        self.assertEqual("1.1", report_doc.version)
