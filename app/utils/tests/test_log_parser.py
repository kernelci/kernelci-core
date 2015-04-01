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
import unittest

import utils.log_parser as lparser


class TestBuildLogParser(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_log_parser_hidden_dir(self):
        job = ".job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(json_obj)

        self.assertEqual(500, status)
        self.assertEqual(1, len(errors.keys()))
        self.assertEqual([500], errors.keys())

    @mock.patch("os.path.isdir")
    def test_log_parser_not_dir(self, mock_isdir):
        mock_isdir.return_value = False

        job = "job"
        kernel = "kernel"
        json_obj = {
            "job": job,
            "kernel": kernel
        }

        status, errors = lparser.parse_build_log(json_obj)

        self.assertEqual(500, status)
        self.assertEqual(1, len(errors.keys()))
        self.assertEqual([500], errors.keys())
