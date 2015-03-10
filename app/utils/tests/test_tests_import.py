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

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_empty(self, mock_db):
        mock_db.return_value = self.db

        case_list = []
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertDictEqual({}, results)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_simple(self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.return_value = (201, "id")

        case_list = [
            {"name": "test-case", "version": "1.0"}
        ]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertDictEqual({}, results)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_complex(self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.return_value = (201, "id")

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}},
            {"name": "test-case1", "version": "1.0", "parameters": {"a": 2}},
            {"name": "test-case2", "version": "1.0", "parameters": {"a": 3}}
        ]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertDictEqual({}, results)

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_save_error(self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.return_value = (500, None)

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}}
        ]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([500], results.keys())

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
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([500], results.keys())
        self.assertEqual(2, len(results[500]))

    @mock.patch("utils.db.save")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_multi_save_error_complex(
            self, mock_db, mock_save):
        mock_db.return_value = self.db
        mock_save.side_effect = [
            (500, None), (201, "id"), (201, "id"), (500, None)]

        case_list = [
            {"name": "test-case0", "version": "1.0", "parameters": {"a": 1}},
            {"name": "test-case1", "version": "1.0", "parameters": {"a": 2}},
            {"name": "test-case2", "version": "1.0", "parameters": {"a": 3}},
            {"name": "test-case3", "version": "1.0", "parameters": {"a": 4}}
        ]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([500], results.keys())
        self.assertEqual(2, len(results[500]))

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_with_non_dictionary(self, mock_db):
        mock_db.return_value = self.db

        case_list = [["foo"]]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([400], results.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_missing_mandatory_keys(self, mock_db):
        mock_db.return_value = self.db

        case_list = [{"parameters": {"a": 1}}]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([400], results.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_multi_test_cases_wrong_key(self, mock_db):
        mock_db.return_value = self.db

        case_list = [{"name": "case", "version": "1.0", "parameters": ["a"]}]
        test_suite_id = "test-suite-id"
        kwargs = {
            "test_set_id": "test-set-id"
        }

        results = tests_import.import_multi_test_case(
            case_list, test_suite_id, {}, **kwargs)

        self.assertListEqual([400], results.keys())
