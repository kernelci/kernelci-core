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
import models.test_suite as mtsuite


class TestTestSuiteModel(unittest.TestCase):

    def test_suite_doc_valid_instance(self):
        test_suite = mtsuite.TestSuiteDocument(
            "name", "lab_name", "build_id", "1.0")
        self.assertIsInstance(test_suite, mbase.BaseDocument)

    def test_suite_doc_to_dict(self):
        test_suite = mtsuite.TestSuiteDocument(
            "name", "lab_name", "build_id", "1.0")

        test_suite.arch = "arm"
        test_suite.board = "board"
        test_suite.board_instance = 1
        test_suite.created_on = "now"
        test_suite.defconfig = "defconfig"
        test_suite.build_id = "another_build-id"
        test_suite.definition_uri = "uri"
        test_suite.git_branch = "git_branch"
        test_suite.id = "id"
        test_suite.job = "job"
        test_suite.job_id = "job_id"
        test_suite.kernel = "kernel"
        test_suite.lab_name = "another_lab"
        test_suite.metadata = {"foo": "bar"}
        test_suite.test_case = ["foo"]
        test_suite.test_set = ["bar"]
        test_suite.time = 10
        test_suite.vcs_commit = "1234"
        test_suite.version = "1.1"

        expected = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "created_on": "now",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig",
            "build_id": "another_build-id",
            "definition_uri": "uri",
            "git_branch": "git_branch",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "lab_name": "another_lab",
            "metadata": {"foo": "bar"},
            "name": "name",
            "test_case": ["foo"],
            "test_set": ["bar"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.1"
        }

        self.assertDictEqual(expected, test_suite.to_dict())

    def test_suite_doc_from_json_missing_key(self):
        test_suite = {
            "_id": "id"
        }

        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(test_suite))

    def test_suite_doc_from_json_wrong_type(self):
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json([]))
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(()))
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(""))

    def test_suite_doc_from_json(self):
        suite_json = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "created_on": "now",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig",
            "build_id": "build-id",
            "definition_uri": "uri",
            "git_branch": "git_branch",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "lab_name": "lab_name",
            "metadata": {"foo": "bar"},
            "name": "name",
            "test_case": ["foo"],
            "test_set": ["bar"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.0"
        }

        test_suite = mtsuite.TestSuiteDocument.from_json(suite_json)

        self.assertIsInstance(test_suite, mtsuite.TestSuiteDocument)
        self.assertDictEqual(suite_json, test_suite.to_dict())

    def test_set_name_setter(self):
        test_suite = mtsuite.TestSuiteDocument(
            "name", "lab_name", "build_id", "1.0")

        def test_name_setter(value):
            test_suite.name = value

        test_name_setter("foo")
        self.assertEqual("foo", test_suite.name)
