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
import unittest

import utils.compare.job


class TestJobCompare(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")

        patcher = mock.patch("utils.db.get_db_connection")
        mock_db = patcher.start()
        mock_db.return_value = self.db
        self.addCleanup(patcher.stop)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_baseline_job_class(self):
        docs = [
            {
                "job_id": "123456789012345678901234",
                "job": "job",
                "kernel": "kernel",
                "git_branch": "git_branch",
                "git_url": "git_url",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "status": "PASS",
                "arch": "arch0"
            },
            {
                "job_id": "123456789012345678901234",
                "job": "job",
                "kernel": "kernel",
                "git_branch": "git_branch",
                "git_url": "git_url",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "status": "FAIL",
                "arch": "arch1"
            }
        ]

        expected_defconfig = {
            ("defconfig0", "defconfig_full0", "arch0"): 0,
            ("defconfig1", "defconfig_full1", "arch1"): 1
        }

        expected_defconfig_status = {
            ("defconfig0", "defconfig_full0", "arch0", "PASS"): 0,
            ("defconfig1", "defconfig_full1", "arch1", "FAIL"): 1
        }

        baseline_job = utils.compare.job.BaselineJob(docs)

        self.assertIsInstance(baseline_job, utils.compare.job.BaselineJob)
        self.assertEqual(2, len(baseline_job.docs))
        self.assertEqual("job", baseline_job.job)
        self.assertEqual("kernel", baseline_job.kernel)
        self.assertEqual("123456789012345678901234", baseline_job.job_id)
        self.assertEqual("git_describe", baseline_job.git_describe)
        self.assertEqual("git_url", baseline_job.git_url)
        self.assertEqual("git_branch", baseline_job.git_branch)
        self.assertEqual("123456", baseline_job.git_commit)
        self.assertEqual(2, baseline_job.total_builds)

        self.assertIsNotNone(baseline_job.baseline_defconfig)
        self.assertIsNotNone(baseline_job.baseline_defconfig_status)

        self.assertDictEqual(
            expected_defconfig, baseline_job.baseline_defconfig)
        self.assertDictEqual(
            expected_defconfig_status, baseline_job.baseline_defconfig_status
        )

    def test_calculate_delta(self):
        self.maxDiff = None
        baseline_docs = [
            {
                "arch": "arch0",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS"
            },
            {
                "arch": "arch1",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "FAIL"
            },
            {
                "arch": "arch3",
                "defconfig": "defconfig3",
                "defconfig_full": "defconfig_full3",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS"
            }
        ]

        compare_docs = [
            {
                "arch": "arch0",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "FAIL"
            },
            {
                "arch": "arch1",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "PASS"
            },
            {
                "arch": "arch2",
                "defconfig": "defconfig2",
                "defconfig_full": "defconfig_full2",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "PASS"
            }
        ]

        expected_data = {
            "git_branch": "compare_git_branch",
            "git_commit": "1234567",
            "git_describe": "compare_git_describe",
            "git_url": "compare_git_url",
            "job": "compare_job",
            "job_id": "123456789012345678901235",
            "kernel": "compare_kernel",
            "total_builds": 3,
            "delta_result": [
                (
                    {
                        "arch": "arch1",
                        "defconfig": "defconfig1",
                        "defconfig_full": "defconfig_full1",
                        "status": "FAIL"
                    },
                    {
                        "arch": "arch1",
                        "defconfig": "defconfig1",
                        "defconfig_full": "defconfig_full1",
                        "status": "PASS"
                    }
                ),
                (
                    {
                        "arch": "arch0",
                        "defconfig": "defconfig0",
                        "defconfig_full": "defconfig_full0",
                        "status": "PASS"
                    },
                    {
                        "arch": "arch0",
                        "defconfig": "defconfig0",
                        "defconfig_full": "defconfig_full0",
                        "status": "FAIL"
                    }
                ),
                (
                    {
                        "arch": "arch3",
                        "defconfig": "defconfig3",
                        "defconfig_full": "defconfig_full3",
                        "status": "PASS"
                    },
                    None
                ),
                (
                    None,
                    {
                        "arch": "arch2",
                        "defconfig": "defconfig2",
                        "defconfig_full": "defconfig_full2",
                        "status": "PASS"
                    }
                )
            ]
        }

        baseline_job = utils.compare.job.BaselineJob(baseline_docs)
        delta_data = utils.compare.job._calculate_delta(
            baseline_job, compare_docs)

        self.assertIsInstance(delta_data, dict)
        self.assertDictEqual(expected_data, delta_data)

    def test_execute_job_delta_wrong(self):
        json_obj = {}

        status_code, result, doc_id, errors = \
            utils.compare.job.execute_job_delta(json_obj, {})

        self.assertEqual(400, status_code)
        self.assertIsNotNone(errors)
        self.assertListEqual([], result)

        json_obj = {
            "job": "job",
            "compare_to": [
                {
                    "job": "job",
                    "kernel": "kernel"
                }
            ]
        }

        status_code, result, doc_id, errors = \
            utils.compare.job.execute_job_delta(json_obj, {})

        self.assertEqual(400, status_code)
        self.assertIsNotNone(errors)
        self.assertListEqual([], result)

        json_obj = {
            "kernel": "kernel",
            "compare_to": [
                {
                    "job": "job",
                    "kernel": "kernel"
                }
            ]
        }

        status_code, result, doc_id, errors = \
            utils.compare.job.execute_job_delta(json_obj, {})

        self.assertEqual(400, status_code)
        self.assertIsNotNone(errors)
        self.assertListEqual([], result)

        json_obj = {
            "kernel": "kernel",
            "job": "job"
        }

        status_code, result, doc_id, errors = \
            utils.compare.job.execute_job_delta(json_obj, {})

        self.assertEqual(400, status_code)
        self.assertIsNotNone(errors)
        self.assertListEqual([], result)

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_job_delta_wrong_wrong_id(self, mock_search):
        mock_search.return_value = None
        json_obj = {
            "job_id": "foo",
            "compare_to": [
                {
                    "job": "job",
                    "kernel": "kernel"
                }
            ]
        }

        status_code, result, doc_id, errors = \
            utils.compare.job.execute_job_delta(json_obj, {})

        self.assertEqual(400, status_code)
        self.assertIsNotNone(errors)
        self.assertListEqual([], result)

    @mock.patch("utils.db.find")
    def test_search_and_compare_no_base(self, mock_find):
        job_id = None
        job = "job"
        kernel = "kernel"
        compare_to = [
            {
                "job": "job",
                "kernel": "kernel"
            }
        ]
        errors = {}

        baseline = {
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "status": "PASS",
        }

        base_docs = mock.MagicMock()
        base_docs.clone = mock.MagicMock()
        base_docs.clone.return_value = [baseline]
        mock_find.return_value = None

        status_code, result = utils.compare.job._search_and_compare(
            job_id, job, kernel, compare_to, errors)

        self.assertEqual(status_code, 404)
        self.assertListEqual(result, [])
        self.assertEqual(1, len(errors.keys()))

    @mock.patch("utils.compare.job._calculate_delta")
    @mock.patch("utils.db.find")
    def test_search_and_compare_valid(self, mock_find, mock_delta):
        job_id = None
        job = "job"
        kernel = "kernel"
        compare_to = [
            {
                "job": "job",
                "kernel": "kernel"
            }
        ]
        errors = {}

        compare_doc = {
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "status": "PASS",
        }

        baseline = {
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "status": "PASS",
        }

        expected = [
            {
                "baseline": {
                    "git_branch": "git_branch",
                    "git_commit": "git_commit",
                    "git_describe": "git_describe",
                    "git_url": "git_url",
                    "job": "job",
                    "job_id": "job_id",
                    "kernel": "kernel",
                    "total_builds": 1
                },
                "result": []
            }
        ]

        base_docs = mock.MagicMock()
        base_docs.clone = mock.MagicMock()
        base_docs.clone.return_value = [baseline]
        mock_find.side_effect = [base_docs, [compare_doc]]
        mock_delta.return_value = []

        status_code, result = utils.compare.job._search_and_compare(
            job_id, job, kernel, compare_to, errors)

        self.assertEqual(status_code, 201)
        self.assertDictEqual(errors, {})
        self.assertListEqual(result, expected)
