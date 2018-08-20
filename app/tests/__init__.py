# Copyright (C) 2014 Linaro Ltd.
#
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

"""Unit tests suite for kernel-ci-backend."""

import unittest


def test_modules():
    return [
        "handlers.common.tests.test_lab",
        "handlers.common.tests.test_query",
        "handlers.common.tests.test_token",
        "handlers.tests.test_batch_handler",
        "handlers.tests.test_bisect_handler",
        "handlers.tests.test_boot_handler",
        "handlers.tests.test_boot_trigger_handler",
        "handlers.tests.test_build_handler",
        "handlers.tests.test_build_logs_handler",
        "handlers.tests.test_callback_handler",
        "handlers.tests.test_compare_handler",
        "handlers.tests.test_count_handler",
        "handlers.tests.test_handler_response",
        "handlers.tests.test_job_handler",
        "handlers.tests.test_job_logs_handler",
        "handlers.tests.test_lab_handler",
        "handlers.tests.test_report_handler",
        "handlers.tests.test_send_handler",
        "handlers.tests.test_stats_handler",
        "handlers.tests.test_test_case_handler",
        "handlers.tests.test_test_suite_handler",
        "handlers.tests.test_token_handler",
        "handlers.tests.test_upload_handler",
        "handlers.tests.test_version_handler",
        "models.tests.test_bisect_model",
        "models.tests.test_boot_model",
        "models.tests.test_build_model",
        "models.tests.test_error_log_model",
        "models.tests.test_error_summary_model",
        "models.tests.test_job_model",
        "models.tests.test_lab_model",
        "models.tests.test_report_model",
        "models.tests.test_stats_model",
        "models.tests.test_test_case_model",
        "models.tests.test_test_suite_model",
        "models.tests.test_token_model",
        "utils.batch.tests.test_batch_common",
        "utils.bisect.tests.test_bisect",
        "utils.boot.tests.test_boot_import",
        "utils.boot.tests.test_boot_regressions",
        "utils.build.tests.test_build_import",
        "utils.compare.tests.test_boot_compare",
        "utils.compare.tests.test_build_compare",
        "utils.compare.tests.test_job_compare",
        "utils.report.tests.test_boot_report",
        "utils.report.tests.test_build_report",
        "utils.report.tests.test_report_common",
        "utils.stats.tests.test_daily_stats",
        "utils.tests.test_base",
        "utils.tests.test_emails",
        "utils.tests.test_log_parser",
        "utils.tests.test_tests_import",
        "utils.tests.test_upload",
        "utils.tests.test_validator"
    ]


def test_suite():
    """Create a unittest.TestSuite object."""
    modules = test_modules()
    suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    for name in modules:
        unit_suite = test_loader.loadTestsFromName(name)
        suite.addTests(unit_suite)
    return suite
