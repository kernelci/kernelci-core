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


import unittest

from mock import patch

from utils.batch.batch_op import (
    BatchBootOperation,
    BatchCountOperation,
    BatchBuildOperation,
    BatchJobOperation,
    BatchOperation,
)
from utils.batch.common import (
    create_batch_operation,
    get_batch_query_args,
)


class TestBatch(unittest.TestCase):

    def test_get_batch_query_args_empty(self):
        query = ""

        self.assertEqual({}, get_batch_query_args(query))

    def test_get_batch_query_base_case(self):
        query = "?foo=bar"
        expected = {"foo": ["bar"]}

        self.assertEqual(expected, get_batch_query_args(query))

    def test_get_batch_query_base_case_wrong(self):
        query = "?foo"

        self.assertEqual({}, get_batch_query_args(query))

    def test_get_batch_query_base_case_wrong_and_correct(self):
        query = "?foo&bar=foo"
        expected = {"bar": ["foo"]}

        self.assertEqual(expected, get_batch_query_args(query))

    def test_get_batch_query_simple_with_question(self):
        query = "?foo=bar&bar=foo"
        expected = {"bar": ["foo"], "foo": ["bar"]}

        self.assertEqual(expected, get_batch_query_args(query))

    def test_get_batch_query_simple_no_question(self):
        query = "foo=bar&bar=foo"
        expected = {"bar": ["foo"], "foo": ["bar"]}

        self.assertEqual(expected, get_batch_query_args(query))

    def test_get_batch_query_multiple_values(self):
        query = "bar=foo&foo=bar&bar=foo&foo=baz&bar=foo"
        expected = {"foo": ["baz", "bar"], "bar": ["foo"]}

        self.assertEqual(expected, get_batch_query_args(query))

    def test_create_batch_op_generic(self):
        json_obj = {
            "collection": "boot",
            "document_id": "doc-id",
            "query": "status=FAIL&job=mainline",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchOperation)

    def test_create_batch_op_count(self):
        json_obj = {
            "collection": "count",
            "document_id": "defconfig",
            "query": "status=FAIL&job=mainline",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchCountOperation)

    def test_create_batch_op_none(self):
        op = create_batch_operation(None, None)
        self.assertIsNone(op)

    def test_create_batch_op_no_collection(self):
        json_obj = {
            "document_id": "defconfig",
            "query": "status=FAIL&job=mainline",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsNone(op)

    @patch('pymongo.MongoClient')
    def test_create_batch_boot_op(self, mocked_mongocl):
        json_obj = {
            "collection": "boot",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchBootOperation)

    @patch('pymongo.MongoClient')
    def test_create_batch_job_op(self, mocked_mongocl):
        json_obj = {
            "collection": "job",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchJobOperation)

    @patch('pymongo.MongoClient')
    def test_create_batch_defconfig_op(self, mocked_mongocl):
        json_obj = {
            "collection": "defconfig",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchBuildOperation)

    @patch('pymongo.MongoClient')
    def test_create_batch_fake_op(self, mocked_mongocl):
        json_obj = {
            "collection": "foo",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchOperation)
