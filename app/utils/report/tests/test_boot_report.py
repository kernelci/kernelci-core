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

"""Test class for the boot email report functions."""

import unittest

import utils.report.boot as breport


class TestBootReport(unittest.TestCase):

    def test_boot_subject_line_no_lab(self):

        kwargs = {
            "job": "a-job",
            "kernel": "a-kernel",
            "lab_name": None,
            "total_count": 10,
            "fail_count": 0,
            "pass_count": 10,
            "untried_count": 0,
            "offline_count": 0
        }

        # All is passed.
        subj = breport._get_boot_subject_string(**kwargs)

        expected = "a-job boot: 10 boots: 0 failed, 10 passed (a-kernel)"
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All failed.
        kwargs["fail_count"] = 10
        kwargs["pass_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = "a-job boot: 10 boots: 10 failed, 0 passed (a-kernel)"
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All offline.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 10

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 0 failed, 0 passed, 10 offline (a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All is untried.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 10

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 0 failed, 0 passed, 10 untried/unknown "
            "(a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed and failed.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 8
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 8 passed (a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and untried.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 7
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 7 passed with 1 untried/unknown "
            "(a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed, untried and offline.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 6 passed with 1 offline, "
            "1 untried/unknown (a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed, untried and offline with conflict.
        kwargs["fail_count"] = 1
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1
        kwargs["conflict_count"] = 2

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 1 failed, 5 passed with 1 offline, "
            "1 untried/unknown, 2 conflicts (a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and offline.
        kwargs["fail_count"] = 3
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 3 failed, 5 passed with 2 offline "
            "(a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and offline with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 5 passed with 2 offline, "
            "1 conflict (a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, fail with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 2

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 6 passed with 2 conflicts "
            "(a-kernel)")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

    def test_boot_subject_line_with_lab(self):

        kwargs = {
            "job": "a-job",
            "kernel": "a-kernel",
            "lab_name": "a-lab",
            "total_count": 10,
            "fail_count": 0,
            "pass_count": 10,
            "untried_count": 0,
            "offline_count": 0
        }

        # All is passed.
        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 0 failed, 10 passed (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All failed.
        kwargs["fail_count"] = 10
        kwargs["pass_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 10 failed, 0 passed (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All offline.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 10

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 0 failed, 0 passed, 10 offline "
            "(a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # All is untried.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 10

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 0 failed, 0 passed, 10 untried/unknown "
            "(a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed and failed.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 8
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 8 passed (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and untried.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 7
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 7 passed with 1 untried/unknown "
            "(a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed, untried and offline.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 6 passed with 1 offline, "
            "1 untried/unknown (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed, untried and offline with conflict.
        kwargs["fail_count"] = 1
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1
        kwargs["conflict_count"] = 2

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 1 failed, 5 passed with 1 offline, "
            "1 untried/unknown, 2 conflicts (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and offline.
        kwargs["fail_count"] = 3
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 0

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 3 failed, 5 passed with 2 offline "
            "(a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, failed and offline with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 1

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 5 passed with 2 offline, "
            "1 conflict (a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)

        # Passed, fail with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 2

        subj = breport._get_boot_subject_string(**kwargs)

        expected = (
            "a-job boot: 10 boots: 2 failed, 6 passed with 2 conflicts "
            "(a-kernel) - a-lab")
        self.assertIsNotNone(subj)
        self.assertEqual(expected, subj)
