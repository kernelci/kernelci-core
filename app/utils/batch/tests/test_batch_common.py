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

from utils.batch.batch_op import (
    BatchBootOperation,
    BatchBuildOperation,
    BatchCountOperation,
    BatchDistinctOperation,
    BatchJobOperation,
    BatchOperation,
    BatchTestCaseOperation,
    BatchTestGroupOperation
)
from utils.batch.common import (
    create_batch_operation,
    get_batch_query_args
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
            "resource": "boot",
            "query": "status=FAIL&job=mainline",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchOperation)

    def test_create_batch_op_count(self):
        json_obj = {
            "resource": "count",
            "document": "build",
            "query": "status=FAIL&job=mainline",
            "operation_id": "op_id"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchCountOperation)
        self.assertEqual("build", op.document)
        self.assertEqual("count", op.resource)
        self.assertEqual("op_id", op.operation_id)

    def test_create_batch_op_none(self):
        op = create_batch_operation(None, None)
        self.assertIsNone(op)

    def test_create_batch_op_no_collection(self):
        json_obj = {
            "resource": "foo",
            "query": "status=FAIL&job=mainline"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsNone(op)

    def test_create_batch_boot_op(self):
        json_obj = {
            "resource": "boot",
            "query": "status=PASS&job=foo",
            "operation_id": "op_id"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchBootOperation)
        self.assertEqual("boot", op.resource)

    def test_create_batch_job_op(self):
        json_obj = {
            "resource": "job",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchJobOperation)
        self.assertEqual("job", op.resource)

    def test_create_batch_build_op(self):
        json_obj = {
            "resource": "build",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchBuildOperation)
        self.assertEqual("build", op.resource)

    def test_create_batch_test_case_op(self):
        json_obj = {
            "resource": "test_case",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchTestCaseOperation)
        self.assertEqual("test_case", op.resource)

    def test_create_batch_test_group_op(self):
        json_obj = {
            "resource": "test_group",
            "query": "status=PASS&job=foo",
            "operation_id": "foo"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchTestGroupOperation)
        self.assertEqual("test_group", op.resource)

    def test_create_batch_distinct(self):
        json_obj = {
            "resource": "boot",
            "distinct": "board",
            "operation_id": "distinct-board"
        }

        op = create_batch_operation(json_obj, {})
        self.assertIsInstance(op, BatchDistinctOperation)
        self.assertEqual("board", op.distinct)
