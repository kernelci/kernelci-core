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
import models.test_case as mtcase


class TestTestCaseModel(unittest.TestCase):

    def test_case_doc_valid_instance(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")
        self.assertIsInstance(test_case, mbase.BaseDocument)
        self.assertEqual(test_case.collection, "test_case")

    def test_case_doc_to_dict(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        test_case.id = "id"
        test_case.attachments = [{"foo": "bar"}]
        test_case.created_on = "now"
        test_case.definition_uri = "scheme://authority/path"
        test_case.index = 1
        test_case.kvm_guest = "kvm_guest"
        test_case.maximum = 1
        test_case.measurements = [{"foo": 1}]
        test_case.metadata = {"foo": "bar"}
        test_case.minimum = -1
        test_case.parameters = {"param": "value"}
        test_case.samples = 10
        test_case.samples_sqr_sum = 1
        test_case.samples_sum = 1
        test_case.status = "FAIL"
        test_case.test_group_id = "another_id"
        test_case.test_group_name = "test-suite"
        test_case.time = 10
        test_case.vcs_commit = "commit_sha"
        test_case.version = "1.1"

        expected = {
            "_id": "id",
            "attachments": [{"foo": "bar"}],
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "index": 1,
            "kvm_guest": "kvm_guest",
            "maximum": 1,
            "measurements": [{"foo": 1}],
            "metadata": {"foo": "bar"},
            "minimum": -1,
            "name": "name",
            "parameters": {"param": "value"},
            "samples": 10,
            "samples_sqr_sum": 1,
            "samples_sum": 1,
            "status": "FAIL",
            "test_group_id": "another_id",
            "test_group_name": "test-suite",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.1"
        }

        self.assertDictEqual(expected, test_case.to_dict())

    def test_case_doc_to_dict_no_id(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        test_case.attachments = [{"foo": "bar"}]
        test_case.created_on = "now"
        test_case.definition_uri = "scheme://authority/path"
        test_case.index = 1
        test_case.kvm_guest = "kvm_guest"
        test_case.maximum = 1
        test_case.measurements = [{"foo": 1}]
        test_case.metadata = {"foo": "bar"}
        test_case.minimum = -1
        test_case.parameters = {"param": "value"}
        test_case.samples = 10
        test_case.samples_sqr_sum = 1
        test_case.samples_sum = 1
        test_case.status = "FAIL"
        test_case.test_group_id = "another_id"
        test_case.test_group_name = "test-suite"
        test_case.time = 10
        test_case.vcs_commit = "commit_sha"
        test_case.version = "1.1"

        expected = {
            "attachments": [{"foo": "bar"}],
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "index": 1,
            "kvm_guest": "kvm_guest",
            "maximum": 1,
            "measurements": [{"foo": 1}],
            "metadata": {"foo": "bar"},
            "minimum": -1,
            "name": "name",
            "parameters": {"param": "value"},
            "samples": 10,
            "samples_sqr_sum": 1,
            "samples_sum": 1,
            "status": "FAIL",
            "test_group_id": "another_id",
            "test_group_name": "test-suite",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.1"
        }

        self.assertDictEqual(expected, test_case.to_dict())

    def test_case_doc_from_json_missing_key(self):
        test_case = {
            "_id": "id"
        }

        self.assertIsNone(mtcase.TestCaseDocument.from_json(test_case))

    def test_case_doc_from_json_wrong_type(self):
        self.assertIsNone(mtcase.TestCaseDocument.from_json([]))
        self.assertIsNone(mtcase.TestCaseDocument.from_json(()))
        self.assertIsNone(mtcase.TestCaseDocument.from_json(""))

    def test_case_doc_from_json(self):
        case_json = {
            "_id": "id",
            "attachments": [{"foo": "bar"}],
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "index": 1,
            "kvm_guest": "kvm_guest",
            "maximum": 1,
            "measurements": [{"foo": 1}],
            "metadata": {"foo": "bar"},
            "minimum": -1,
            "name": "name",
            "parameters": {"param": "value"},
            "samples": 10,
            "samples_sqr_sum": 1,
            "samples_sum": 1,
            "status": "FAIL",
            "test_group_id": "another_id",
            "test_group_name": "test-suite",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.1"
        }

        test_case = mtcase.TestCaseDocument.from_json(case_json)

        self.assertIsInstance(test_case, mtcase.TestCaseDocument)
        self.assertDictEqual(case_json, test_case.to_dict())

    def test_case_doc_parameters_setter(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def parameters_setter(value):
            test_case.parameters = value

        self.assertRaises(ValueError, parameters_setter, ["foo"])
        self.assertRaises(ValueError, parameters_setter, ("foo"))
        self.assertRaises(ValueError, parameters_setter, "foo")

        parameters_setter([])
        self.assertDictEqual({}, test_case.parameters)
        parameters_setter(())
        self.assertDictEqual({}, test_case.parameters)
        parameters_setter(None)
        self.assertDictEqual({}, test_case.parameters)
        parameters_setter("")
        self.assertDictEqual({}, test_case.parameters)

    def test_case_doc_attachments_setter(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def attachments_setter(value):
            test_case.attachments = value

        self.assertRaises(ValueError, attachments_setter, {"foo": "bar"})
        self.assertRaises(ValueError, attachments_setter, "foo")

        attachments_setter([])
        self.assertListEqual([], test_case.attachments)
        attachments_setter(())
        self.assertListEqual([], test_case.attachments)
        attachments_setter(None)
        self.assertListEqual([], test_case.attachments)
        attachments_setter("")
        self.assertListEqual([], test_case.attachments)
        attachments_setter({})
        self.assertListEqual([], test_case.attachments)

    def test_case_doc_add_attachments(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def add_attachment(value):
            test_case.add_attachment(value)

        test_case.attachments = [{"foo": "bar"}]
        test_case.add_attachment({"baz": "foo"})

        expected = [{"foo": "bar"}, {"baz": "foo"}]
        self.assertListEqual(expected, test_case.attachments)

        self.assertRaises(ValueError, add_attachment, "")
        self.assertRaises(ValueError, add_attachment, [])
        self.assertRaises(ValueError, add_attachment, {})
        self.assertRaises(ValueError, add_attachment, ())

    def test_case_doc_measurements_setter(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def measurements_setter(value):
            test_case.measurements = value

        self.assertRaises(ValueError, measurements_setter, {"foo": "bar"})
        self.assertRaises(ValueError, measurements_setter, "foo")

        measurements_setter([])
        self.assertListEqual([], test_case.measurements)
        measurements_setter(())
        self.assertListEqual([], test_case.measurements)
        measurements_setter(None)
        self.assertListEqual([], test_case.measurements)
        measurements_setter("")
        self.assertListEqual([], test_case.measurements)
        measurements_setter({})
        self.assertListEqual([], test_case.measurements)

    def test_case_doc_add_measurement(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def add_measurement(value):
            test_case.add_measurement(value)

        test_case.measurements = [{"foo": "bar"}]
        test_case.add_measurement({"baz": "foo"})

        expected = [{"foo": "bar"}, {"baz": "foo"}]
        self.assertListEqual(expected, test_case.measurements)

        self.assertRaises(ValueError, add_measurement, "")
        self.assertRaises(ValueError, add_measurement, [])
        self.assertRaises(ValueError, add_measurement, {})
        self.assertRaises(ValueError, add_measurement, ())

    def test_case_doc_set_status(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def set_status(value):
            test_case.status = value

        self.assertEqual("PASS", test_case.status)
        self.assertRaises(ValueError, set_status, "FOO")
        self.assertRaises(ValueError, set_status, "")
        self.assertRaises(ValueError, set_status, 1)
        self.assertRaises(ValueError, set_status, {})
        self.assertRaises(ValueError, set_status, [])
        self.assertRaises(ValueError, set_status, ())

    def test_set_name_setter(self):
        test_case = mtcase.TestCaseDocument("name", "test_suite_id", "1.0")

        def test_name_setter(value):
            test_case.name = value

        test_name_setter("foo")
        self.assertEqual("foo", test_case.name)
