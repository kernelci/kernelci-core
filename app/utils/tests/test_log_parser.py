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
import mock
import mongomock
import os
import shutil
import tempfile
import types
import unittest

import models.build as mbuild
import utils
import utils.log_parser as lparser


class TestBuildLogParser(unittest.TestCase):

    def setUp(self):
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_parse_build_log(self):
        build_dir = None
        errors = {}

        try:
            build_doc = mbuild.BuildDocument(
                "job", "kernel", "defconfig", "branch", "build_environment")
            build_dir = tempfile.mkdtemp()
            log_file = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "assets", "build_log_0.log")

            status, e_l, w_l, m_l = lparser._parse_log(
                build_doc, log_file, build_dir, errors)

            self.assertEqual(200, status)

            self.assertIsInstance(errors, types.DictionaryType)
            self.assertIsInstance(e_l, types.ListType)
            self.assertIsInstance(w_l, types.ListType)
            self.assertIsInstance(m_l, types.ListType)

            self.assertEqual(0, len(errors.keys()))
            self.assertEqual(22, len(e_l))
            self.assertEqual(8, len(w_l))
            self.assertEqual(0, len(m_l))
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    def test_parse_build_log_no_file(self):
        build_dir = None
        errors = {}
        try:
            build_doc = mbuild.BuildDocument(
                "job", "kernel", "defconfig", "branch", "build_environment")
            build_dir = tempfile.mkdtemp()
            log_file = os.path.join(build_dir, utils.BUILD_LOG_FILE)

            status, e_l, w_l, m_l = lparser._parse_log(
                build_doc, log_file, build_dir, errors)

            self.assertEqual(500, status)

            self.assertIsInstance(errors, types.DictionaryType)
            self.assertIsInstance(e_l, types.ListType)
            self.assertIsInstance(w_l, types.ListType)
            self.assertIsInstance(m_l, types.ListType)

            self.assertDictEqual({}, errors)
            self.assertEqual(0, len(e_l))
            self.assertEqual(0, len(w_l))
            self.assertEqual(0, len(m_l))
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_one_error(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "errors": [
                (1, "foo")
            ],
            "warnings": [],
            "mismatches": []
        }
        errors = {
            "foo": 3
        }
        expected_list = [
            (4, "foo")
        ]
        lparser._update_prev_summary(prev_doc, errors, None, None, self.db)
        self.assertListEqual(expected_list, prev_doc["errors"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_more_errors(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "errors": [
                (1, "foo"), (2, "bar")
            ],
            "warnings": [],
            "mismatches": []
        }
        errors = {
            "foo": 3,
            "baz": 1
        }
        expected_list = [
            (4, "foo"), (2, "bar"), (1, "baz")
        ]
        lparser._update_prev_summary(prev_doc, errors, None, None, self.db)
        self.assertListEqual(expected_list, prev_doc["errors"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_one_warning(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "warnings": [
                (1, "foo")
            ],
            "errors": [],
            "mismatches": []
        }
        warnings = {
            "foo": 3
        }
        expected_list = [
            (4, "foo")
        ]
        lparser._update_prev_summary(prev_doc, None, warnings, None, self.db)
        self.assertListEqual(expected_list, prev_doc["warnings"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_more_warning(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "warnings": [
                (1, "foo"), (2, "bar")
            ],
            "errors": [],
            "mismatches": []
        }
        warnings = {
            "foo": 3,
            "baz": 1
        }
        expected_list = [
            (4, "foo"), (2, "bar"), (1, "baz")
        ]
        lparser._update_prev_summary(prev_doc, None, warnings, None, self.db)
        self.assertListEqual(expected_list, prev_doc["warnings"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_one_mismatch(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "mismatches": [
                (1, "foo")
            ],
            "errors": [],
            "warnings": []
        }
        mismatches = {
            "foo": 3
        }
        expected_list = [
            (4, "foo")
        ]
        lparser._update_prev_summary(prev_doc, None, None, mismatches, self.db)
        self.assertListEqual(expected_list, prev_doc["mismatches"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_simple_with_more_mismatches(
            self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "mismatches": [
                (1, "foo"), (2, "bar")
            ],
            "errors": [],
            "warnings": []
        }
        mismatches = {
            "foo": 3,
            "baz": 1
        }
        expected_list = [
            (4, "foo"), (2, "bar"), (1, "baz")
        ]
        lparser._update_prev_summary(prev_doc, None, None, mismatches, self.db)
        self.assertListEqual(expected_list, prev_doc["mismatches"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_complex(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "errors": [
                (1, "foo"), (2, "baz"), (3, "foobar")
            ],
            "mismatches": [
                (1, "foo"), (2, "bar")
            ],
            "warnings": []
        }
        errors = {
            "bazfoo": 1
        }
        mismatches = {
            "foo": 3,
            "baz": 1
        }
        expected_err_list = [
            (3, "foobar"), (2, "baz"), (1, "foo"), (1, "bazfoo")
        ]
        expected_mism_list = [
            (4, "foo"), (2, "bar"), (1, "baz")
        ]
        lparser._update_prev_summary(
            prev_doc, errors, None, mismatches, self.db)
        self.assertListEqual(expected_err_list, prev_doc["errors"])
        self.assertListEqual(expected_mism_list, prev_doc["mismatches"])

    @mock.patch("utils.db.find_and_update")
    def test_update_prev_summary_complex_all(self, mock_update):
        mock_update.return_value = 200
        prev_doc = {
            "_id": "doc-id",
            "warnings": [
                (2, "warn")
            ],
            "errors": [
                (1, "foo"), (2, "baz"), (3, "foobar")
            ],
            "mismatches": [
                (1, "foo"), (2, "bar")
            ]
        }
        warnings = {
            "warn": 3,
            "new-warn": 1
        }
        errors = {
            "bazfoo": 1
        }
        mismatches = {
            "foo": 3,
            "baz": 1
        }
        expected_warn_list = [
            (5, "warn"), (1, "new-warn")
        ]
        expected_err_list = [
            (3, "foobar"), (2, "baz"), (1, "foo"), (1, "bazfoo")
        ]
        expected_mism_list = [
            (4, "foo"), (2, "bar"), (1, "baz")
        ]
        lparser._update_prev_summary(
            prev_doc, errors, warnings, mismatches, self.db)
        self.assertListEqual(expected_err_list, prev_doc["errors"])
        self.assertListEqual(expected_mism_list, prev_doc["mismatches"])
        self.assertListEqual(expected_warn_list, prev_doc["warnings"])
