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
import mock

import models.base as mbase
import models.report as mreport


class TestReportModel(unittest.TestCase):

    def test_report_document_valid_instance(self):
        report_doc = mreport.ReportDocument("name")
        self.assertIsInstance(report_doc, mbase.BaseDocument)

    def test_report_collection_name(self):
        report_doc = mreport.ReportDocument("name")
        self.assertEqual("report", report_doc.collection)

    def test_report_setter(self):
        report_doc = mreport.ReportDocument("name")
        report_doc.created_on = "now"
        report_doc.version = "foo"
        self.assertEqual("name", report_doc.name)
        self.assertEqual("now", report_doc.created_on)
        self.assertEqual("foo", report_doc.version)

    def test_report_to_dict_simple(self):
        report_doc = mreport.ReportDocument("report")
        report_doc.created_on = "now"

        expected = {
            "created_on": "now",
            "errors": [],
            "job": None,
            "kernel": None,
            "git_branch": None,
            "name": "report",
            "status": None,
            "type": None,
            "updated_on": None,
            "version": "1.1"
        }
        self.assertDictEqual(expected, report_doc.to_dict())

    @mock.patch("datetime.datetime")
    def test_report_document_to_dict(self, mock_date):
        mock_date.now = mock.MagicMock()
        mock_date.now.return_value = "now"

        report_doc = mreport.ReportDocument("name")
        report_doc.id = "id"
        report_doc.job = "job"
        report_doc.git_branch = "branch"
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
            "git_branch": "branch",
            "name": "name",
            "status": "ERROR",
            "type": "boot",
            "updated_on": "now",
            "version": "1.1"
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

    def test_report_document_from_json_wrong(self):
        self.assertIsNone(mreport.ReportDocument.from_json([]))
        self.assertIsNone(mreport.ReportDocument.from_json(()))
        self.assertIsNone(mreport.ReportDocument.from_json(""))
        self.assertIsNone(mreport.ReportDocument.from_json({}))
