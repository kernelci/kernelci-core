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

import logging
import mongomock
import unittest
import mock

import utils.tests_import as tests_import


class TestTestsImport(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_empty(self, mock_db, mock_update):
        mock_db.return_value = self.db
        mock_update.return_value = 200

        case_list = []
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertDictEqual({}, errors)
        self.assertListEqual([], ids)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_simple(
            self, mock_db, mock_save, mock_update):
        mock_db.return_value = self.db
        mock_save.return_value = (201, "fake-id")
        mock_update.return_value = 200

        case_list = [
            {"name": "test-case", "version": "1.0"}
        ]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertDictEqual({}, errors)
        self.assertListEqual(["fake-id"], ids)

    @mock.patch("utils.db.update")
    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_complex(
            self, mock_db, mock_save, mock_update):
        mock_db.return_value = self.db
        mock_save.side_effect = [(201, "id0"), (201, "id1"), (201, "id2")]
        mock_update.return_value = 200

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}},
            {"name": "test-case1", "version": "1.0", "parameters": {"a": 2}},
            {"name": "test-case2", "version": "1.0", "parameters": {"a": 3}}
        ]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertDictEqual({}, errors)
        self.assertListEqual(["id0", "id1", "id2"], ids)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_save_error(self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.return_value = (500, None)

        case_list = [
            {
                "name": "test-case0",
                "test_group_id": "test-suite-id",
                "version": "1.0", "parameters": {"a": 1}}
        ]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([500], errors.keys())
        self.assertListEqual([], ids)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_multi_save_error(
            self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.return_value = (500, None)

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}},
            {"name": "test-case1", "version": "1.0", "parameters": {"a": 2}}
        ]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([500], errors.keys())
        self.assertEqual(2, len(errors[500]))
        self.assertListEqual([], ids)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_multi_save_error_complex(
            self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.side_effect = [
            (500, None), (201, "id0"), (201, "id1"), (500, None)]

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}},
            {"name": "test-case1", "version": "1.0", "parameters": {"a": 2}},
            {"name": "test-case2", "version": "1.0", "parameters": {"a": 3}},
            {"name": "test-case3", "version": "1.0", "parameters": {"a": 4}}
        ]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([500], errors.keys())
        self.assertEqual(2, len(errors[500]))
        self.assertListEqual(["id0", "id1"], ids)

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_non_dictionary(self, mock_db):
        mock_db.return_value = self.db

        case_list = [["foo"]]
        test_group_id = "test-suite-id"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([400], errors.keys())
        self.assertListEqual([], ids)

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_missing_mandatory_keys(self, mock_db):
        mock_db.return_value = self.db

        case_list = [{"parameters": {"a": 1}}]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([400], errors.keys())
        self.assertListEqual([], ids)

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_wrong_key(self, mock_db):
        mock_db.return_value = self.db

        case_list = [{"name": "case", "version": "1.0", "parameters": ["a"]}]
        test_group_id = "0123456789ab0123456789ab"
        kwargs = {}

        ids, errors = tests_import.import_multi_test_cases(
            case_list, test_group_id, "suite-name", {}, **kwargs)

        self.assertListEqual([400], errors.keys())
        self.assertListEqual([], ids)

    @mock.patch("utils.tests_import.parse_test_group")
    def test_update_test_group_simple(self, mock_parse):
        mock_parse.return_value = {}
        suite_json = {
            "name": "test-suite",
            "build_id": "build-id",
            "version": "1.0",
            "time": 100
        }
        test_group_id = "test-suite-id"

        ret_val, doc = tests_import.update_test_group(
            suite_json, test_group_id, {})

        self.assertEqual(ret_val, 200)
        self.assertDictEqual({}, doc)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.update")
    @mock.patch("utils.db.get_db_connection")
    @mock.patch("utils.tests_import.parse_test_group")
    def test_update_test_group_with_result(
            self, mock_parse, mock_db, mock_update, mock_id):
        mock_parse.return_value = {"_id": "fake"}
        mock_db.return_value = self.db
        mock_update.return_value = 200
        mock_id.return_value = "fake"
        suite_json = {
            "name": "test-suite",
            "build_id": "build-id",
            "version": "1.0",
            "time": 100
        }
        test_group_id = "test-suite-id"

        ret_val, doc = tests_import.update_test_group(
            suite_json, test_group_id, {})

        self.assertEqual(ret_val, 200)
        self.assertDictEqual({"_id": "fake"}, doc)

    @mock.patch("utils.db.find_one2")
    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.get_db_connection")
    def test_parse_test_group_with_all(self, mock_db, mock_id, mock_find):
        build_doc = {
            "_id": "build-id",
            "job": None,
            "kernel": "kernel",
            "defconfig": None
        }

        boot_doc = {
            "_id": "boot-id",
            "board": "board",
            "board_instance": "instance",
            "job": None
        }

        job_doc = {
            "_id": "job-id",
            "job": "job"
        }
        mock_db.return_value = self.db
        mock_id.side_effect = ["build-id", "boot-id", "job-id"]
        mock_find.side_effect = [build_doc, boot_doc, job_doc]

        suite_json = {
            "board": None,
            "board_instance": None,
            "boot_id": "boot-id",
            "build_id": "build-id",
            "job_id": "job-id",
            "name": "test-suite",
            "time": 100,
            "version": "1.0"
        }

        expected = {
            "board": "board",
            "board_instance": "instance",
            "boot_id": "boot-id",
            "build_id": "build-id",
            "job": "job",
            "job_id": "job-id",
            "kernel": "kernel"
        }

        doc = tests_import.parse_test_group(suite_json, {})
        self.assertDictEqual(expected, doc)

    @mock.patch("utils.db.get_db_connection")
    def test_parse_test_group_with_nothing(self, mock_db):
        mock_db.return_value = self.db

        suite_json = {
            "board": None,
            "board_instance": None,
            "name": "test-suite",
            "time": 100,
            "version": "1.0"
        }

        doc = tests_import.parse_test_group(suite_json, {})
        self.assertDictEqual({}, doc)

    @mock.patch("bson.objectid.ObjectId")
    @mock.patch("utils.db.get_db_connection")
    def test_parse_test_group_with_all_in_suite(self, mock_db, mock_id):
        mock_db.return_value = self.db
        mock_id.side_effect = ["build-id", "boot-id", "job-id"]

        suite_json = {
            "arch": "arch",
            "board": "board",
            "board_instance": "instance",
            "boot_id": "boot-id",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "build_id": "build-id",
            "job": "job",
            "job_id": "job-id",
            "kernel": "kernel",
            "name": "test-suite",
            "time": 100,
            "version": "1.0"
        }

        expected = {
            "boot_id": "boot-id",
            "build_id": "build-id",
            "job_id": "job-id"
        }

        doc = tests_import.parse_test_group(suite_json, {})
        self.assertDictEqual(expected, doc)
