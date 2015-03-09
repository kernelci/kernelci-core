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
import models.test_set as mtset


class TestTestSetModel(unittest.TestCase):

    def test_set_doc_valid_instance(self):
        test_set = mtset.TestSetDocument("name", "test_suite_id", "1.0")
        self.assertIsInstance(test_set, mbase.BaseDocument)
        self.assertEqual(test_set.collection, "test_set")

    def test_set_doc_to_dict(self):
        test_set = mtset.TestSetDocument("name", "test_suite_id", "1.0")

        test_set.created_on = "now"
        test_set.definition_uri = "scheme://authority/path"
        test_set.id = "id"
        test_set.metadata = {"foo": "bar"}
        test_set.parameters = {"param": "value"}
        test_set.test_case = [{"foo": "bar"}]
        test_set.time = 10
        test_set.vcs_commit = "commit_sha"
        test_set.version = "1.1"
        test_set.test_suite_id = "another_id"

        expected = {
            "_id": "id",
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "metadata": {"foo": "bar"},
            "name": "name",
            "parameters": {"param": "value"},
            "test_case": [{"foo": "bar"}],
            "test_suite_id": "another_id",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.1"
        }

        self.assertDictEqual(expected, test_set.to_dict())

    def test_set_doc_to_dict_no_id(self):
        test_set = mtset.TestSetDocument("name", "test_suite_id", "1.0")

        test_set.created_on = "now"
        test_set.definition_uri = "scheme://authority/path"
        test_set.metadata = {"foo": "bar"}
        test_set.parameters = {"param": "value"}
        test_set.test_case = [{"foo": "bar"}]
        test_set.time = 10
        test_set.vcs_commit = "commit_sha"

        expected = {
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "metadata": {"foo": "bar"},
            "name": "name",
            "parameters": {"param": "value"},
            "test_case": [{"foo": "bar"}],
            "test_suite_id": "test_suite_id",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.0"
        }

        self.assertDictEqual(expected, test_set.to_dict())

    def test_set_doc_from_json_missing_key(self):
        test_set = {
            "_id": "id",
            "version": "1.0",
            "test_suite_id": "test_suite_id"
        }

        self.assertIsNone(mtset.TestSetDocument.from_json(test_set))

    def test_set_doc_from_json_wrong_type(self):
        self.assertIsNone(mtset.TestSetDocument.from_json([]))
        self.assertIsNone(mtset.TestSetDocument.from_json(()))
        self.assertIsNone(mtset.TestSetDocument.from_json(""))

    def test_set_doc_from_json(self):
        set_json = {
            "_id": "id",
            "created_on": "now",
            "definition_uri": "scheme://authority/path",
            "metadata": {"foo": "bar"},
            "name": "name",
            "parameters": {"param": "value"},
            "test_case": [{"foo": "bar"}],
            "test_suite_id": "test_suite_id",
            "time": 10,
            "vcs_commit": "commit_sha",
            "version": "1.0",
        }

        test_suite = mtset.TestSetDocument.from_json(set_json)

        self.assertIsInstance(test_suite, mtset.TestSetDocument)
        self.assertDictEqual(set_json, test_suite.to_dict())

    def test_set_doc_parameters_setter(self):
        test_set = mtset.TestSetDocument("name", "test_suite_id", "1.0")

        def parameters_setter(value):
            test_set.parameters = value

        self.assertRaises(ValueError, parameters_setter, ["foo"])
        self.assertRaises(ValueError, parameters_setter, ("foo"))
        self.assertRaises(ValueError, parameters_setter, "foo")

        parameters_setter([])
        self.assertDictEqual({}, test_set.parameters)
        parameters_setter(())
        self.assertDictEqual({}, test_set.parameters)
        parameters_setter(None)
        self.assertDictEqual({}, test_set.parameters)
        parameters_setter("")
        self.assertDictEqual({}, test_set.parameters)

    def test_set_doc_test_case_setter(self):
        test_set = mtset.TestSetDocument("name", "test_suite_id", "1.0")

        def test_case_setter(value):
            test_set.test_case = value

        self.assertRaises(ValueError, test_case_setter, {"foo": "bar"})
        self.assertRaises(ValueError, test_case_setter, "foo")

        test_case_setter([])
        self.assertListEqual([], test_set.test_case)
        test_case_setter(())
        self.assertListEqual([], test_set.test_case)
        test_case_setter(None)
        self.assertListEqual([], test_set.test_case)
        test_case_setter("")
        self.assertListEqual([], test_set.test_case)
