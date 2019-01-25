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
import mongomock
import tempfile
import unittest

import models.test_group
import utils.kci_test
import utils.kci_test.regressions


class TestTests(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self._db = mongomock.Database(mongomock.Connection(), "kernel-ci")

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _save_group_assert(self, data, db):
        err = {}
        doc_id = utils.kci_test.import_and_save_test_group(data, None, db, err)
        if err:
            print(err)
        self.assertIsNotNone(doc_id)
        return doc_id

    def _make_test_data(self, git_commit, test_series):
        test_cases = list({
            models.NAME_KEY: name,
            models.STATUS_KEY: status,
            models.TIME_KEY: 123456789.0,  # ToDo: make optional
        } for name, status in test_series)
        group_data = {
            models.NAME_KEY: "dummy",
            models.LAB_NAME_KEY: "unit-test-lab",
            models.JOB_KEY: "unittest",
            models.KERNEL_KEY: "v0.0-unit-test-{}".format(git_commit),
            models.GIT_COMMIT_KEY: git_commit,
            models.GIT_BRANCH_KEY: "master",
            models.ARCHITECTURE_KEY: "gothic",
            models.DEVICE_TYPE_KEY: "some-fake-device",
            models.DEFCONFIG_KEY: "defconfig",
            models.DEFCONFIG_FULL_KEY: "defconfig",
            models.TEST_CASES_KEY: test_cases,
            models.BUILD_ENVIRONMENT_KEY: "concrete",
        }
        # ToDo: remove BOARD_KEY as it's redundant, use DEVICE_TYPE_KEY instead
        group_data[models.BOARD_KEY] = group_data[models.DEVICE_TYPE_KEY]
        # ToDo: make TIME_KEY not required
        group_data[models.TIME_KEY] = 123456789.0
        return group_data

    def test_import_test_group(self):
        group_collection = self._db[models.TEST_GROUP_COLLECTION]
        case_collection = self._db[models.TEST_CASE_COLLECTION]

        git_commit = "abcdef123456"
        test_cases_data = [
            ("foo", "PASS"),
            ("bar", "FAIL"),
            ("baz", "PASS"),
        ]
        group_data = self._make_test_data(git_commit, test_cases_data)
        test_case_list = group_data[models.TEST_CASES_KEY]

        group_id = self._save_group_assert(group_data, self._db)
        group_doc = utils.db.find_one2(group_collection, group_id)
        self.assertIsNotNone(group_doc)
        del group_data[models.TIME_KEY]
        del group_data[models.TEST_CASES_KEY]
        self.assertDictContainsSubset(group_data, group_doc)
        test_cases = group_doc[models.TEST_CASES_KEY]
        self.assertEqual(len(test_cases), len(test_cases_data))
        test_case_docs = [utils.db.find_one2(case_collection, case_id)
                          for case_id in test_cases]
        for ref, doc in zip(test_case_list, test_case_docs):
            del ref[models.TIME_KEY]
            self.assertDictContainsSubset(ref, doc)

    def test_new_failure(self):
        group_collection = self._db[models.TEST_GROUP_COLLECTION]
        regr_collection = self._db[models.TEST_REGRESSION_COLLECTION]

        # First results: all passing
        first_git_commit = "1234abcd"
        group_data = self._make_test_data(first_git_commit, [
            ("first-test", "PASS"),
            ("second-test", "PASS"),
        ])
        group_id = self._save_group_assert(group_data, self._db)
        ret, regr_ids = utils.kci_test.regressions.find(group_id, db=self._db)
        self.assertEqual(ret, 200)
        self.assertEqual(regr_ids, [])
        first_group = utils.db.find_one2(group_collection, group_id)
        self.assertIsNotNone(first_group)
        first_test_cases = first_group[models.TEST_CASES_KEY]
        self.assertEqual(len(first_test_cases), 2)

        # Second results: one failing test case
        second_git_commit = "1234abce"
        group_data[models.TEST_CASES_KEY][1][models.STATUS_KEY] = "FAIL"
        group_data.update({
            models.KERNEL_KEY: "v0.0-unit-test-001",
            models.GIT_COMMIT_KEY: second_git_commit,
        })
        group_id = self._save_group_assert(group_data, self._db)
        ret, regr_ids = utils.kci_test.regressions.find(group_id, db=self._db)
        self.assertEqual(ret, 200)
        self.assertEqual(len(regr_ids), 1)
        second_group = utils.db.find_one2(group_collection, group_id)
        self.assertIsNotNone(second_group)
        second_test_cases = second_group[models.TEST_CASES_KEY]
        self.assertEqual(len(second_test_cases), 2)

        # Get and check regression data
        regr_id = regr_ids[0]
        regr_doc = utils.db.find_one2(regr_collection, regr_id)
        self.assertIsNotNone(regr_doc)
        regr_list = regr_doc[models.REGRESSIONS_KEY]
        self.assertEqual(len(regr_list), 2)
        ref_list = [
            {
                models.STATUS_KEY: "PASS",
                models.GIT_COMMIT_KEY: first_git_commit,
                models.TEST_CASE_ID_KEY: first_test_cases[1],
                models.KERNEL_KEY: first_group[models.KERNEL_KEY],
            },
            {
                models.STATUS_KEY: "FAIL",
                models.GIT_COMMIT_KEY: second_git_commit,
                models.TEST_CASE_ID_KEY: second_test_cases[1],
                models.KERNEL_KEY: second_group[models.KERNEL_KEY],
            },
        ]
        for regr, ref in zip(regr_list, ref_list):
            self.assertDictContainsSubset(ref, regr)

    def test_no_regression(self):
        group_collection = self._db[models.TEST_GROUP_COLLECTION]
        regr_collection = self._db[models.TEST_REGRESSION_COLLECTION]

        # First results: all passing
        first_git_commit = "1234abcf"
        group_data = self._make_test_data(first_git_commit, [
            ("test-a", "PASS"),
            ("test-b", "PASS"),
        ])
        group_id = self._save_group_assert(group_data, self._db)
        ret, regr_ids = utils.kci_test.regressions.find(group_id, db=self._db)
        self.assertEqual(ret, 200)
        self.assertEqual(regr_ids, [])

        # Second results: all passing too
        second_git_commit = "1234abd0"
        group_data.update({
            models.KERNEL_KEY: "v0.0-unit-test-001",
            models.GIT_COMMIT_KEY: second_git_commit,
        })
        group_id = self._save_group_assert(group_data, self._db)
        ret, regr_ids = utils.kci_test.regressions.find(group_id, db=self._db)
        self.assertEqual(ret, 200)
        self.assertEqual(regr_ids, [])

    def test_tracking_regression(self):
        group_collection = self._db[models.TEST_GROUP_COLLECTION]
        regr_collection = self._db[models.TEST_REGRESSION_COLLECTION]

        scenario = [
            {
                "commit": "4567890a",
                "tests": [
                    ("test-001", "PASS"),
                    ("test-002", "PASS"),
                    ("test-003", "PASS"),
                    ("test-004", "FAIL"),
                ],
                "regressions": [],
            },
            {
                "commit": "4567890b",
                "tests": [
                    ("test-002", "FAIL"),
                    ("test-003", "PASS"),
                    ("test-004", "FAIL"),
                ],
                "regressions": ["dummy.test-002"],
            },
            {
                "commit": "4567890c",
                "tests": [
                    ("test-001", "PASS"),
                    ("test-002", "FAIL"),
                    ("test-003", "FAIL"),
                ],
                "regressions": ["dummy.test-002", "dummy.test-003"],
            },
            {
                "commit": "4567890d",
                "tests": [
                    ("test-001", "PASS"),
                    ("test-002", "FAIL"),
                    ("test-003", "PASS"),
                    ("test-004", "FAIL"),
                ],
                "regressions": ["dummy.test-002"],
            },
        ]

        for stage in scenario:
            group_data = self._make_test_data(stage["commit"], stage["tests"])
            group_id = self._save_group_assert(group_data, self._db)
            ret, regrs = utils.kci_test.regressions.find(group_id, db=self._db)
            self.assertEqual(ret, 200)
            regr_ref = stage["regressions"]
            self.assertEqual(len(regrs), len(regr_ref))
            for regr_id in regrs:
                regr_doc = utils.db.find_one2(regr_collection, regr_id)
                self.assertIsNotNone(regr_doc)
                test_case_path = ".".join(regr_doc[models.HIERARCHY_KEY])
                self.assertIn(test_case_path, regr_ref)
