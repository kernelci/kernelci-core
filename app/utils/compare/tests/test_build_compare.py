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

import copy
import logging
import mock
import mongomock
import unittest

import utils.compare.build


class TestBuildCompare(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")

        patcher = mock.patch("utils.db.get_db_connection")
        mock_db = patcher.start()
        mock_db.return_value = self.db
        self.addCleanup(patcher.stop)

        self.baseline = {
            "job": "job",
            "kernel": "kernel",
            "arch": "arch",
            "defconfig_full": "defconfig_full",
        }

        self.baseline_return = {
            "job": "job",
            "kernel": "kernel",
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "dtb_dir_data": [
                "foo.dtb", "bar.dtb", "baz.dtb"
            ],
            "status": "PASS"
        }

        self.compare_to = [
            {
                "job": "job",
                "kernel": "kernel",
                "arch": "arch",
                "defconfig": "defconfig",
                "defconfig_full": "defconfig_full",
                "dtb_dir_data": [
                    "foo.dtb"
                ],
                "status": "PASS"
            }
        ]

        self.compare_return = {
            "job": "job",
            "kernel": "kernel",
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "dtb_dir_data": [
                "foo.dtb"
            ],
            "status": "PASS"
        }

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_execute_build_delta_empty(self):
        status, result, doc_id, errors = utils.compare.build.execute_delta(
            {}, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    def test_execute_build_delta_no_compare_targets(self):
        status, result, doc_id, errors = utils.compare.build.execute_delta(
            self.baseline, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_build_delta_wrong_id(self, mock_search):
        mock_search.return_value = None
        json_obj = {
            "build_id": "1234",
            "compare_to": self.compare_to
        }

        status, result, doc_id, errors = utils.compare.build.execute_delta(
            json_obj, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_build_delta_not_found(self, mock_search):
        mock_search.return_value = None
        json_obj = self.baseline
        json_obj["compare_to"] = self.compare_to

        status, result, doc_id, errors = utils.compare.build.execute_delta(
            json_obj, db_options={})

        self.assertEqual(404, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([404], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_build_delta_wrong_compare_to(self, mock_search):
        mock_search.return_value = None

        collection = self.db["build"]
        collection.find_one = mock.MagicMock()
        collection.find_one.return_value = self.baseline_return

        json_obj = self.baseline

        json_obj["compare_to"] = [
            {
                "bar": "bar",
                "baz": "baz",
                "foo": "foo"
            }
        ]

        status, result, doc_id, errors = utils.compare.build.execute_delta(
            json_obj, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.compare.common.save_delta_doc")
    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_build_delta(self, mock_search, mock_save):
        mock_search.return_value = None
        mock_save.return_value = "1234567890"

        collection = self.db["build"]
        collection.find_one = mock.MagicMock()
        collection.find_one.side_effect = [
            self.baseline_return, self.compare_return]

        json_obj = self.baseline
        json_obj["compare_to"] = self.compare_to

        baseline_result = copy.deepcopy(self.baseline_return)
        baseline_result["dtb_dir_data"] = 3

        compare_result = copy.deepcopy(self.compare_return)
        compare_result["dtb_dir_data"] = 1

        expected = [{
            "baseline": baseline_result,
            "compared": [
                compare_result
            ]
        }]

        status, result, doc_id, errors = utils.compare.build.execute_delta(
            json_obj, db_options={})

        self.assertEqual(201, status)
        self.assertListEqual(expected, result)
