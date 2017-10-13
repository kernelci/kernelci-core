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

EXP_01 = \
    u"a-job/a-branch boot: 10 boots: 0 failed, 10 passed (a-kernel)"
EXP_02 = \
    u"a-job/a-branch boot: 10 boots: 10 failed, 0 passed (a-kernel)"
EXP_03 = \
    u"a-job/a-branch boot: 10 boots: 0 failed, 0 passed, 10 offline (a-kernel)"
EXP_04 = (
    u"a-job/a-branch boot: 10 boots: 0 failed, 0 passed, 10 untried/unknown "
    u"(a-kernel)")
EXP_05 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 8 passed (a-kernel)")
EXP_06 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 7 passed with 1 "
    u"untried/unknown (a-kernel)")
EXP_07 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 6 passed with 1 offline, "
    u"1 untried/unknown (a-kernel)")
EXP_08 = (
    u"a-job/a-branch boot: 10 boots: 1 failed, 5 passed with 1 offline, "
    u"1 untried/unknown, 2 conflicts (a-kernel)")
EXP_09 = (
    u"a-job/a-branch boot: 10 boots: 3 failed, 5 passed with 2 offline "
    u"(a-kernel)")
EXP_10 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 5 passed with 2 offline, "
    u"1 conflict (a-kernel)")
EXP_11 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 6 passed with 2 conflicts "
    u"(a-kernel)")

EXP_12 = (
    u"a-job/a-branch boot: 10 boots: 0 failed, 10 passed (a-kernel) "
    u"- a-lab")
EXP_13 = (
    u"a-job/a-branch boot: 10 boots: 10 failed, 0 passed (a-kernel) "
    u"- a-lab")
EXP_14 = (
    u"a-job/a-branch boot: 10 boots: 0 failed, 0 passed, 10 offline "
    u"(a-kernel) - a-lab")
EXP_15 = (
    u"a-job/a-branch boot: 10 boots: 0 failed, 0 passed, 10 untried/unknown "
    u"(a-kernel) - a-lab")
EXP_16 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 8 passed (a-kernel) "
    u"- a-lab")
EXP_17 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 7 passed with 1 "
    u"untried/unknown (a-kernel) - a-lab")
EXP_18 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 6 passed with 1 offline, "
    u"1 untried/unknown (a-kernel) - a-lab")
EXP_19 = (
    u"a-job/a-branch boot: 10 boots: 1 failed, 5 passed with 1 offline, "
    u"1 untried/unknown, 2 conflicts (a-kernel) - a-lab")
EXP_20 = (
    u"a-job/a-branch boot: 10 boots: 3 failed, 5 passed with 2 offline "
    u"(a-kernel) - a-lab")
EXP_21 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 5 passed with 2 offline, "
    u"1 conflict (a-kernel) - a-lab")
EXP_22 = (
    u"a-job/a-branch boot: 10 boots: 2 failed, 6 passed with 2 conflicts "
    u"(a-kernel) - a-lab")


class TestBootReport(unittest.TestCase):

    def test_boot_subject_line_no_lab(self):

        kwargs = {
            "job": "a-job",
            "kernel": "a-kernel",
            "git_branch": "a-branch",
            "lab_name": None,
            "total_count": 10,
            "fail_count": 0,
            "pass_count": 10,
            "untried_count": 0,
            "offline_count": 0
        }

        # All is passed.
        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_01, subj)

        # All failed.
        kwargs["fail_count"] = 10
        kwargs["pass_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_02, subj)

        # All offline.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 10

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_03, subj)

        # All is untried.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 10

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_04, subj)

        # Passed and failed.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 8
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_05, subj)

        # Passed, failed and untried.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 7
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_06, subj)

        # Passed, failed, untried and offline.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_07, subj)

        # Passed, failed, untried and offline with conflict.
        kwargs["fail_count"] = 1
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1
        kwargs["conflict_count"] = 2

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_08, subj)

        # Passed, failed and offline.
        kwargs["fail_count"] = 3
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_09, subj)

        # Passed, failed and offline with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_10, subj)

        # Passed, fail with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 2

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_11, subj)

    def test_boot_subject_line_with_lab(self):

        kwargs = {
            "job": "a-job",
            "kernel": "a-kernel",
            "git_branch": "a-branch",
            "lab_name": "a-lab",
            "total_count": 10,
            "fail_count": 0,
            "pass_count": 10,
            "untried_count": 0,
            "offline_count": 0
        }

        # All is passed.
        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_12, subj)

        # All failed.
        kwargs["fail_count"] = 10
        kwargs["pass_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_13, subj)

        # All offline.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 10

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_14, subj)

        # All is untried.
        kwargs["fail_count"] = 0
        kwargs["pass_count"] = 0
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 10

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_15, subj)

        # Passed and failed.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 8
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_16, subj)

        # Passed, failed and untried.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 7
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_17, subj)

        # Passed, failed, untried and offline.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_18, subj)

        # Passed, failed, untried and offline with conflict.
        kwargs["fail_count"] = 1
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 1
        kwargs["untried_count"] = 1
        kwargs["conflict_count"] = 2

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_19, subj)

        # Passed, failed and offline.
        kwargs["fail_count"] = 3
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 0

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_20, subj)

        # Passed, failed and offline with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 5
        kwargs["offline_count"] = 2
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 1

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_21, subj)

        # Passed, fail with conflicts.
        kwargs["fail_count"] = 2
        kwargs["pass_count"] = 6
        kwargs["offline_count"] = 0
        kwargs["untried_count"] = 0
        kwargs["conflict_count"] = 2

        subj = breport.get_boot_subject_string(kwargs)

        self.assertIsNotNone(subj)
        self.assertEqual(EXP_22, subj)
