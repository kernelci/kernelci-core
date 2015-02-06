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

"""Test class for the email report functions."""

import unittest

import utils.report.common as rcommon


class TestReportCommon(unittest.TestCase):

    def test_count_unique_with_string(self):
        to_count = ""
        self.assertEqual(0, rcommon.count_unique(to_count))

    def test_count_unique_with_dict(self):
        to_count = {}
        self.assertEqual(0, rcommon.count_unique(to_count))

    def test_count_unique_with_list(self):
        to_count = [None, "a", "b", None]
        self.assertEqual(2, rcommon.count_unique(to_count))

    def test_count_unique_with_tuple(self):
        to_count = (None, "a", "b", None, None, None, "c")
        self.assertEqual(3, rcommon.count_unique(to_count))

    def test_parse_job_results_empty(self):
        results = [{}]
        self.assertIsNone(rcommon.parse_job_results(results))

    def test_parse_job_results_with_git_commit(self):
        results = [{"git_commit": "12345"}]
        expected = {
            "git_commit": "12345",
            "git_branch": "Unknown",
            "git_url": "Unknown"
        }
        self.assertDictEqual(expected, rcommon.parse_job_results(results))

    def test_parse_job_results_with_git_branch(self):
        results = [{"git_branch": "branch"}]
        expected = {
            "git_commit": "Unknown",
            "git_branch": "branch",
            "git_url": "Unknown"
        }
        self.assertDictEqual(expected, rcommon.parse_job_results(results))

    def test_parse_job_results_with_git_url(self):
        results = [{"git_url": "url"}]
        expected = {
            "git_commit": "Unknown",
            "git_branch": "Unknown",
            "git_url": "url"
        }
        self.assertDictEqual(expected, rcommon.parse_job_results(results))

    def test_parse_job_results_with_git_all(self):
        results = [
            {"git_url": "url", "git_commit": "12345", "git_branch": "branch"}]
        expected = {
            "git_commit": "12345",
            "git_branch": "branch",
            "git_url": "url"
        }
        self.assertDictEqual(expected, rcommon.parse_job_results(results))
