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

import utils.compare.boot


class TestBootCompare(unittest.TestCase):

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
            "board": "board",
            "lab_name": "lab"
        }

        self.baseline_return = {
            "job": "job",
            "kernel": "kernel",
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "board": "board",
            "lab_name": "lab",
            "status": "PASS"
        }

        self.compare_to = [
            {
                "job": "job",
                "kernel": "kernel",
                "arch": "arch",
                "defconfig": "defconfig",
                "defconfig_full": "defconfig_full",
                "board": "board",
                "lab_name": "lab",
                "status": "PASS"
            }
        ]

        self.compare_return = {
            "job": "job",
            "kernel": "kernel",
            "arch": "arch",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "board": "board",
            "lab_name": "lab",
            "status": "PASS"
        }

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_execute_boot_delta_empty(self):
        status, result, doc_id, errors = utils.compare.boot.execute_delta(
            {}, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    def test_execute_boot_delta_no_compare_targets(self):
        status, result, doc_id, errors = utils.compare.boot.execute_delta(
            self.baseline, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_boot_delta_wrong_id(self, mock_search):
        mock_search.return_value = None
        json_obj = {
            "boot_id": "1234",
            "compare_to": self.compare_to
        }

        status, result, doc_id, errors = utils.compare.boot.execute_delta(
            json_obj, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_boot_delta_not_found(self, mock_search):
        mock_search.return_value = None
        json_obj = self.baseline
        json_obj["compare_to"] = self.compare_to

        status, result, doc_id, errors = utils.compare.boot.execute_delta(
            json_obj, db_options={})

        self.assertEqual(404, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([404], errors.keys())

    @mock.patch("utils.compare.common.search_saved_delta_doc")
    def test_execute_boot_delta_wrong_compare_to(self, mock_search):
        mock_search.return_value = None

        collection = self.db["boot"]
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

        status, result, doc_id, errors = utils.compare.boot.execute_delta(
            json_obj, db_options={})

        self.assertEqual(400, status)
        self.assertListEqual([], result)
        self.assertIsNone(doc_id)
        self.assertListEqual([400], errors.keys())
