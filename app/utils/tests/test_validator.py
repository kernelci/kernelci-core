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

import json
import unittest

from utils.validator import (
    is_valid_json,
    is_valid_batch_json,
)


class TestValidator(unittest.TestCase):

    def test_valid_json_valid(self):
        json_string = '{"job": "job", "kernel": "kernel"}'
        accepted_keys = ('job', 'kernel')

        self.assertTrue(
            is_valid_json(json.loads(json_string), accepted_keys)
        )

    def test_valid_json_valid_job(self):
        json_string = '{"job": "job"}'
        accepted_keys = ('job', 'kernel')

        self.assertTrue(
            is_valid_json(json.loads(json_string), accepted_keys)
        )

    def test_valid_json_only_kernel(self):
        json_string = '{"kernel": "kernel"}'
        accepted_keys = ('job', 'kernel')

        self.assertTrue(
            is_valid_json(json.loads(json_string), accepted_keys)
        )

    def test_not_valid_json(self):
        json_string = '{"kernel": "foo", "foo": "bar"}'
        accepted_keys = ('job', 'kernel')

        self.assertFalse(
            is_valid_json(json.loads(json_string), accepted_keys)
        )


class TestBatchValidator(unittest.TestCase):

    def test_is_valid_batch_json_empty(self):
        json_string = '{}'
        batch_key = 'batch'
        accepted_keys = ()

        self.assertFalse(
            is_valid_batch_json(
                json.loads(json_string), batch_key, accepted_keys
            )
        )

    def test_valid_batch_simple_from_obj(self):
        batch_key = 'batch'
        accepted_keys = ("method", "operation_id", "collection", "query")

        json_obj = {
            "batch": [
                {
                    "method": "GET",
                    "operation_id": "foo",
                    "collection": "bar",
                    "query": "fuz"
                },
                {
                    "method": "GET",
                    "collection": "baz",
                }
            ]
        }

        self.assertTrue(
            is_valid_batch_json(json_obj, batch_key, accepted_keys)
        )

    def test_valid_batch_json_from_string(self):
        batch_key = 'batch'
        accepted_keys = ("method", "operation_id", "collection", "query")

        json_str = (
            '{"batch": [{"method": "GET"}, {"method": "GET"}]}'
        )

        self.assertTrue(
            is_valid_batch_json(json.loads(json_str), batch_key, accepted_keys)
        )
