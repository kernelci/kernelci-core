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

import utils.report.build as breport


class TestBuildReport(unittest.TestCase):

    def test_build_subject_string(self):

        kwargs = {
            "fail_count": 0,
            "total_count": 10,
            "errors_count": 0,
            "warnings_count": 0,
            "kernel": "a-kernel",
            "job": "a-job",
            "pass_count": 10
        }

        # No errors, no warnings.
        subject = breport._get_build_subject_string(**kwargs)
        expected = u"a-job build: 10 builds: 0 failed, 10 passed (a-kernel)"

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Some warnings, no errors (singular).
        kwargs["warnings_count"] = 1

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, "
            "1 warning (a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Some warnings, no errors (plural).
        kwargs["warnings_count"] = 10

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, "
            "10 warnings (a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Warnings and errors (plural).
        kwargs["errors_count"] = 10
        kwargs["warnings_count"] = 10

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, 10 errors, "
            "10 warnings (a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Warnings and errors (singular).
        kwargs["errors_count"] = 1
        kwargs["warnings_count"] = 1

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, 1 error, "
            "1 warning (a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Errors, no warnings (singular).
        kwargs["errors_count"] = 1
        kwargs["warnings_count"] = 0

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, 1 error "
            "(a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)

        # Errors, no warnings (plural).
        kwargs["errors_count"] = 10
        kwargs["warnings_count"] = 0

        subject = breport._get_build_subject_string(**kwargs)
        expected = (
            u"a-job build: 10 builds: 0 failed, 10 passed, 10 errors "
            "(a-kernel)")

        self.assertIsNotNone(subject)
        self.assertEqual(expected, subject)
