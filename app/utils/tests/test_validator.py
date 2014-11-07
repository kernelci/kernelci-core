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

import utils.validator as utilsv


class TestValidator(unittest.TestCase):

    def test_valid_json_valid(self):
        json_string = '{"job": "job", "kernel": "kernel"}'
        accepted_keys = ['job', 'kernel']

        valid, reason = utilsv.is_valid_json(
            json.loads(json_string), accepted_keys
        )
        self.assertTrue(valid)
        self.assertIsNone(reason)

    def test_valid_json_with_more_valid_keys(self):
        json_string = '{"kernel": "kernel"}'
        accepted_keys = ['job', 'kernel', "defconfig", "foo"]

        valid, reason = utilsv.is_valid_json(
            json.loads(json_string), accepted_keys
        )
        self.assertTrue(valid)
        self.assertIsNone(reason)

    def test_valid_json_with_strange_keys(self):
        json_obj = {
            "kernel": "foo",
            "foo": "bar",
            "baz": "foo",
            "job": "job",
        }
        expected = {
            "kernel": "foo",
            "job": "job",
        }
        accepted_keys = ['job', 'kernel']

        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)

        self.assertTrue(valid)
        self.assertIsNotNone(reason)
        self.assertDictEqual(expected, json_obj)

    def test_no_accepted_keys(self):
        json_obj = {
            "kernel": "foo",
            "job": "job",
            "foo": "bar"
        }
        accepted_keys = None

        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)
        self.assertFalse(valid)
        self.assertIsNotNone(reason)

    def test_remove_all_keys(self):
        json_obj = {
            "job": "job",
            "kernel": "kernel",
        }

        accepted_keys = ["foo", "bar"]
        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)

        self.assertFalse(valid)
        self.assertIsNotNone(reason)

    def test_validation_complex_valid_no_reason(self):
        accepted_keys = {
            "mandatory": [
                "job",
                "kernel"
            ],
            "accepted": [
                "foo",
                "bar",
                "baz",
                "job",
                "kernel",
            ]
        }

        json_obj = {
            "job": "job",
            "kernel": "kernel",
            "foo": "foo"
        }

        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)

        self.assertTrue(valid)
        self.assertIsNone(reason)

    def test_validation_complex_valid_with_reason(self):
        accepted_keys = {
            "mandatory": [
                "job",
                "kernel"
            ],
            "accepted": [
                "baz",
                "job",
                "kernel",
            ]
        }

        json_obj = {
            "job": "job",
            "kernel": "kernel",
            "foo": "foo"
        }

        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)

        self.assertTrue(valid)
        self.assertIsNotNone(reason)

    def test_validation_complex_no_mandatory(self):
        accepted_keys = {
            "mandatory": [
                "job",
                "kernel"
            ],
            "accepted": [
                "baz",
                "job",
                "kernel",
            ]
        }

        json_obj = {
            "foo": "foo"
        }

        valid, reason = utilsv.is_valid_json(json_obj, accepted_keys)

        self.assertFalse(valid)
        self.assertIsNotNone(reason)


class TestBatchValidator(unittest.TestCase):

    def test_is_valid_batch_json_empty(self):
        json_string = '{}'
        batch_key = 'batch'
        accepted_keys = ()

        self.assertFalse(
            utilsv.is_valid_batch_json(
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
            utilsv.is_valid_batch_json(json_obj, batch_key, accepted_keys)
        )

    def test_valid_batch_json_from_string(self):
        batch_key = 'batch'
        accepted_keys = ("method", "operation_id", "collection", "query")

        json_str = (
            '{"batch": [{"method": "GET"}, {"method": "GET"}]}'
        )

        self.assertTrue(
            utilsv.is_valid_batch_json(
                json.loads(json_str), batch_key, accepted_keys
            )
        )

    def test_non_valid_batch_json_from_dict(self):
        batch_key = 'batch'
        accepted_keys = ("method", "operation_id", "collection", "query")

        json_obj = {
            "batch": [
                ["foo"], ["bar"]
            ]
        }

        self.assertFalse(
            utilsv.is_valid_batch_json(json_obj, batch_key, accepted_keys)
        )

        json_obj = {
            "batch": [
                "foo", "bar"
            ]
        }

        self.assertFalse(
            utilsv.is_valid_batch_json(json_obj, batch_key, accepted_keys)
        )

    def test_non_valid_batch_json_wrong_keys(self):
        batch_key = 'batch'
        accepted_keys = ("method", "operation_id", "collection", "query")

        json_obj = {
            "batch": [
                {
                    "foo_method": "GET",
                },
                {
                    "method": "GET",
                    "collection": "baz",
                }
            ]
        }

        self.assertFalse(
            utilsv.is_valid_batch_json(json_obj, batch_key, accepted_keys)
        )
