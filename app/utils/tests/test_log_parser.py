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
import os
import shutil
import tempfile
import types
import unittest

import utils.log_parser as lparser


class TestBuildLogParser(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @mock.patch("utils.log_parser._traverse_dir_and_parse")
    def test_log_parser_correct(self, mock_parse):
        mock_parse.return_value = (200, {})
        job_id = "job_id"
        job = "job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(job_id, json_obj, {})

        self.assertEqual(200, status)
        self.assertDictEqual({}, errors)

    def test_log_parser_no_job_id(self):
        job_id = None
        job = "job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(job_id, json_obj, {})

        self.assertEqual(500, status)
        self.assertEqual(1, len(errors.keys()))
        self.assertEqual([500], errors.keys())

    def test_log_parser_hidden_dir(self):
        job_id = "job_id"
        job = ".job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(job_id, json_obj, {})

        self.assertEqual(500, status)
        self.assertEqual(1, len(errors.keys()))
        self.assertEqual([500], errors.keys())

    @mock.patch("os.path.isdir")
    def test_log_parser_not_dir(self, mock_isdir):
        mock_isdir.return_value = False

        job_id = "job_id"
        job = "job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(job_id, json_obj, {})

        self.assertEqual(500, status)
        self.assertEqual(1, len(errors.keys()))
        self.assertEqual([500], errors.keys())

    def test_parse_build_log(self):
        build_dir = None
        errors = {}

        try:
            build_dir = tempfile.mkdtemp()
            log_file = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "assets", "build_log_0.log")

            status, e_l, w_l, m_l = lparser._parse_log(
                "job", "kernel", "defconfig", log_file, build_dir, errors)

            self.assertEqual(200, status)

            self.assertIsInstance(errors, types.DictionaryType)
            self.assertIsInstance(e_l, types.ListType)
            self.assertIsInstance(w_l, types.ListType)
            self.assertIsInstance(m_l, types.ListType)

            self.assertEqual(0, len(errors.keys()))
            self.assertEqual(9, len(e_l))
            self.assertEqual(2, len(w_l))
            self.assertEqual(0, len(m_l))
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    def test_parse_build_log_no_file(self):
        build_dir = None
        errors = {}
        try:
            build_dir = tempfile.mkdtemp()

            status, e_l, w_l, m_l = lparser._parse_log(
                "job", "kernel", "defconfig", build_dir, build_dir, errors)

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

    @mock.patch("io.open", create=True)
    def test_parse_build_log_error_opening(self, mock_open):
        mock_open.side_effect = IOError
        build_dir = None
        errors = {}
        try:
            build_dir = tempfile.mkdtemp()
            log_file = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "assets", "build_log_0.log")

            status, e_l, w_l, m_l = lparser._parse_log(
                "job", "kernel", "defconfig", log_file, build_dir, errors)

            self.assertEqual(500, status)

            self.assertIsInstance(errors, types.DictionaryType)
            self.assertIsInstance(e_l, types.ListType)
            self.assertIsInstance(w_l, types.ListType)
            self.assertIsInstance(m_l, types.ListType)

            self.assertEqual(1, len(errors.keys()))
            self.assertEqual([500], errors.keys())
            self.assertEqual(0, len(e_l))
            self.assertEqual(0, len(w_l))
            self.assertEqual(0, len(m_l))
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)
