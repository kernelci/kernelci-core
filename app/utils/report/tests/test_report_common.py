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

    def test_translate_git_url_not_knownw(self):
        git_url = "git://foo.bar/path"
        commit_id = "12345"

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        self.assertIsNone(translated_url)

    def test_translate_git_url_known_no_commit(self):
        git_url = (
            "git://git.kernel.org/pub/scm/linux/kernel"
            "/git/next/linux-next.git")

        translated_url = rcommon.translate_git_url(git_url)
        expected = (
            "https://git.kernel.org/cgit/linux/kernel/git/next/linux-next.git")

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)

    def test_translate_git_url_known_with_commit(self):
        git_url = (
            "git://git.kernel.org/pub/scm/linux/kernel"
            "/git/next/linux-next.git")
        commit_id = "12345"

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        expected = (
            "https://git.kernel.org/cgit/linux/kernel/git/"
            "next/linux-next.git/commit/?id=12345")

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)

    def test_translate_git_linaro_url_known_with_commit(self):
        git_url = "git://git.linaro.org/lava-team/kernel-ci-backend.git"
        commit_id = "12345"

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        expected = (
            "https://git.linaro.org/lava-team/"
            "kernel-ci-backend.git/commit/?id=12345")

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)

    def test_translate_git_linaro_url_known_no_commit(self):
        git_url = "git://git.linaro.org/lava-team/kernel-ci-backend.git"
        commit_id = None

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        expected = "https://git.linaro.org/lava-team/kernel-ci-backend.git"

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)

    def test_translate_android_url_known_with_commit(self):
        git_url = "https://android.googlesource.com/kernel/common"
        commit_id = "1234"

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        expected = "https://android.googlesource.com/kernel/common/+/1234"

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)

    def test_translate_android_url_known_with_no_commit(self):
        git_url = "https://android.googlesource.com/kernel/common"
        commit_id = None

        translated_url = rcommon.translate_git_url(
            git_url, commit_id=commit_id)

        expected = "https://android.googlesource.com/kernel/common"

        self.assertIsNotNone(translated_url)
        self.assertEqual(expected, translated_url)
