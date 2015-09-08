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
import types
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

        baseline_job = utils.compare.job.CompareJob(docs)

        self.assertIsInstance(baseline_job, utils.compare.job.CompareJob)
        self.assertEqual(2, len(baseline_job.docs))
        self.assertEqual("job", baseline_job.job)
        self.assertEqual("kernel", baseline_job.kernel)
        self.assertEqual("123456789012345678901234", baseline_job.job_id)
        self.assertEqual("git_describe", baseline_job.git_describe)
        self.assertEqual("git_url", baseline_job.git_url)
        self.assertEqual("git_branch", baseline_job.git_branch)
        self.assertEqual("123456", baseline_job.git_commit)
        self.assertEqual(2, baseline_job.total_docs)

        self.assertIsNotNone(baseline_job.defconfig)
        self.assertIsNotNone(baseline_job.defconfig_status)

        self.assertDictEqual(expected_defconfig, baseline_job.defconfig)
        self.assertDictEqual(
            expected_defconfig_status, baseline_job.defconfig_status)

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

        mock_find.return_value = None

        status_code, result = utils.compare.job._search_and_compare(
            job_id, job, kernel, compare_to, errors, {})

        self.assertEqual(status_code, 404)
        self.assertListEqual(result, [])
        self.assertEqual(1, len(errors.keys()))

    @mock.patch("utils.db.find")
    def test_search_and_compare_valid(self, mock_find):
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
            "_id": "0",
            "arch": "arch",
            "created_on": "today",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "status": "PASS"
        }

        baseline = {
            "_id": "0",
            "arch": "arch",
            "created_on": "yesterday",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "status": "PASS"
        }

        expected = [
            {
                "baseline": {
                    "created_on": "yesterday",
                    "git_branch": "git_branch",
                    "git_commit": "git_commit",
                    "git_describe": "git_describe",
                    "git_url": "git_url",
                    "job": "job",
                    "job_id": "job_id",
                    "kernel": "kernel",
                    "total_builds": 1
                },
                "compare_to": [
                    {
                        "created_on": "today",
                        "git_branch": "git_branch",
                        "git_commit": "git_commit",
                        "git_describe": "git_describe",
                        "git_url": "git_url",
                        "job": "job",
                        "job_id": "job_id",
                        "kernel": "kernel",
                        "total_builds": 1
                    }
                ],
                "delta_result": []
            }
        ]

        base_docs = mock.MagicMock()
        base_docs.clone = mock.MagicMock()
        base_docs.clone.return_value = [baseline]
        compare_docs = mock.MagicMock()
        compare_docs.clone = mock.MagicMock()
        compare_docs.clone.return_value = [compare_doc]
        mock_find.side_effect = [base_docs, compare_docs]

        status_code, result = utils.compare.job._search_and_compare(
            job_id, job, kernel, compare_to, errors, {})

        self.assertEqual(status_code, 201)
        self.assertDictEqual(errors, {})
        self.assertListEqual(result, expected)

    def test_n_way_compare_one_compare(self):
        self.maxDiff = None
        baseline_docs = [
            {
                "arch": "arch",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "0"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "FAIL",
                "_id": "1"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig3",
                "defconfig_full": "defconfig_full3",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "2"
            }
        ]

        compare_docs = [
            {
                "arch": "arch",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "FAIL",
                "_id": "0"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "PASS",
                "_id": "1"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig2",
                "defconfig_full": "defconfig_full2",
                "git_branch": "compare_git_branch",
                "git_commit": "1234567",
                "git_describe": "compare_git_describe",
                "git_url": "compare_git_url",
                "job": "compare_job",
                "job_id": "123456789012345678901235",
                "kernel": "compare_kernel",
                "status": "PASS",
                "_id": "2"
            }
        ]

        exp_delta_data = [
            (
                ("defconfig0", "defconfig_full0", "arch"),
                [("PASS", "0"), ("FAIL", "0")]),
            (
                ("defconfig1", "defconfig_full1", "arch"),
                [("FAIL", "1"), ("PASS", "1")]),
            (
                ("defconfig2", "defconfig_full2", "arch"),
                [None, ("PASS", "2")]),
            (
                ("defconfig3", "defconfig_full3", "arch"),
                [("PASS", "2"), None])
        ]

        baseline = utils.compare.job.CompareJob(baseline_docs)
        compare_to = utils.compare.job.CompareJob(compare_docs)

        compare_data, delta_data = utils.compare.job._n_way_compare(
            baseline, [compare_to])

        self.assertIsInstance(compare_data, types.ListType)
        self.assertIsInstance(delta_data, types.ListType)

        self.assertEqual(1, len(compare_data))
        self.assertListEqual(exp_delta_data, delta_data)

    def test_n_way_compare_two_compare(self):
        self.maxDiff = None
        baseline_docs = [
            {
                "arch": "arch",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "0"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "FAIL",
                "_id": "1"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig3",
                "defconfig_full": "defconfig_full3",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "2"
            }
        ]

        compare_docs = [
            [
                {
                    "arch": "arch",
                    "defconfig": "defconfig0",
                    "defconfig_full": "defconfig_full0",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "FAIL",
                    "_id": "0"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig1",
                    "defconfig_full": "defconfig_full1",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "PASS",
                    "_id": "1"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig2",
                    "defconfig_full": "defconfig_full2",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "PASS",
                    "_id": "2"
                }
            ],
            [
                {
                    "arch": "arch",
                    "defconfig": "defconfig0",
                    "defconfig_full": "defconfig_full0",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "PASS",
                    "_id": "0"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig2",
                    "defconfig_full": "defconfig_full2",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "PASS",
                    "_id": "1"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig3",
                    "defconfig_full": "defconfig_full3",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "FAIL",
                    "_id": "2"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig4",
                    "defconfig_full": "defconfig_full4",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "FAIL",
                    "_id": "3"
                }
            ]
        ]

        exp_delta_data = [
            (("defconfig0", "defconfig_full0", "arch"),
                [("PASS", "0"), ("FAIL", "0"), ("PASS", "0")]),
            (("defconfig1", "defconfig_full1", "arch"),
                [("FAIL", "1"), ("PASS", "1"), None]),
            (("defconfig2", "defconfig_full2", "arch"),
                [None, ("PASS", "2"), ("PASS", "1")]),
            (("defconfig3", "defconfig_full3", "arch"),
                [("PASS", "2"), None, ("FAIL", "2")]),
            (("defconfig4", "defconfig_full4", "arch"),
                [None, None, ("FAIL", "3")])
        ]

        baseline = utils.compare.job.CompareJob(baseline_docs)
        compare_to = []
        for doc in compare_docs:
            compare_to.append(utils.compare.job.CompareJob(doc))

        compare_data, delta_data = utils.compare.job._n_way_compare(
            baseline, compare_to)

        self.assertIsInstance(compare_data, types.ListType)
        self.assertIsInstance(delta_data, types.ListType)

        self.assertEqual(2, len(compare_data))
        self.assertListEqual(exp_delta_data, delta_data)

    def test_n_way_compare_three_compare(self):
        self.maxDiff = None
        baseline_docs = [
            {
                "arch": "arch",
                "defconfig": "defconfig0",
                "defconfig_full": "defconfig_full0",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "0"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig1",
                "defconfig_full": "defconfig_full1",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "FAIL",
                "_id": "1"
            },
            {
                "arch": "arch",
                "defconfig": "defconfig3",
                "defconfig_full": "defconfig_full3",
                "git_branch": "git_branch",
                "git_commit": "123456",
                "git_describe": "git_describe",
                "git_url": "git_url",
                "job": "job",
                "job_id": "123456789012345678901234",
                "kernel": "kernel",
                "status": "PASS",
                "_id": "2"
            }
        ]

        compare_docs = [
            [
                {
                    "arch": "arch",
                    "defconfig": "defconfig0",
                    "defconfig_full": "defconfig_full0",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "FAIL",
                    "_id": "0"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig1",
                    "defconfig_full": "defconfig_full1",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "PASS",
                    "_id": "1"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig2",
                    "defconfig_full": "defconfig_full2",
                    "git_branch": "compare_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_0",
                    "job_id": "123456789012345678901235",
                    "kernel": "compare_kernel_0",
                    "status": "PASS",
                    "_id": "2"
                }
            ],
            [
                {
                    "arch": "arch",
                    "defconfig": "defconfig0",
                    "defconfig_full": "defconfig_full0",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "PASS",
                    "_id": "0"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig2",
                    "defconfig_full": "defconfig_full2",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "PASS",
                    "_id": "1"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig3",
                    "defconfig_full": "defconfig_full3",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "FAIL",
                    "_id": "2"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig4",
                    "defconfig_full": "defconfig_full4",
                    "git_branch": "compare_1_git_branch",
                    "git_commit": "1234567",
                    "git_describe": "compare_1_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_1",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_1",
                    "status": "FAIL",
                    "_id": "3"
                }
            ],
            [
                {
                    "arch": "arch3",
                    "defconfig": "defconfig5",
                    "defconfig_full": "defconfig_full5",
                    "git_branch": "compare_2_git_branch",
                    "git_commit": "123456",
                    "git_describe": "compare_2_git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_2",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_2",
                    "status": "FAIL",
                    "_id": "0"
                },
                {
                    "arch": "arch",
                    "defconfig": "defconfig0",
                    "defconfig_full": "defconfig_full0",
                    "git_branch": "git_branch",
                    "git_commit": "123456",
                    "git_describe": "git_describe",
                    "git_url": "compare_git_url",
                    "job": "compare_job_2",
                    "job_id": "123456789012345678901236",
                    "kernel": "compare_kernel_2",
                    "status": "FAIL",
                    "_id": "1"
                },
            ]
        ]

        exp_delta_data = [
            (("defconfig0", "defconfig_full0", "arch"),
                [("PASS", "0"), ("FAIL", "0"), ("PASS", "0"), ("FAIL", "1")]),
            (("defconfig1", "defconfig_full1", "arch"),
                [("FAIL", "1"), ("PASS", "1"), None, None]),
            (("defconfig2", "defconfig_full2", "arch"),
                [None, ("PASS", "2"), ("PASS", "1"), None]),
            (("defconfig3", "defconfig_full3", "arch"),
                [("PASS", "2"), None, ("FAIL", "2"), None]),
            (("defconfig4", "defconfig_full4", "arch"),
                [None, None, ("FAIL", "3"), None]),
            (("defconfig5", "defconfig_full5", "arch3"),
                [None, None, None, ("FAIL", "0")]),
        ]

        baseline = utils.compare.job.CompareJob(baseline_docs)
        compare_to = []
        for doc in compare_docs:
            compare_to.append(utils.compare.job.CompareJob(doc))

        compare_data, delta_data = utils.compare.job._n_way_compare(
            baseline, compare_to)

        self.assertIsInstance(compare_data, types.ListType)
        self.assertIsInstance(delta_data, types.ListType)

        self.assertEqual(3, len(compare_data))
        self.assertListEqual(exp_delta_data, delta_data)
