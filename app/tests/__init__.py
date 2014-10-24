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
        'handlers.tests.test_batch_handler',
        'handlers.tests.test_bisect_handler',
        'handlers.tests.test_boot_handler',
        'handlers.tests.test_count_handler',
        'handlers.tests.test_defconf_handler',
        'handlers.tests.test_handler_response',
        'handlers.tests.test_handlers_common',
        'handlers.tests.test_job_handler',
        'handlers.tests.test_subscription_handler',
        'handlers.tests.test_token_handler',
        'models.tests.test_boot_model',
        'models.tests.test_models',
        'models.tests.test_token_model',
        'utils.batch.tests.test_batch_common',
        'utils.tests.test_bootimport',
        'utils.tests.test_docimport',
        'utils.tests.test_meta_parser',
        'utils.tests.test_subscribe',
        'utils.tests.test_validator',
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
