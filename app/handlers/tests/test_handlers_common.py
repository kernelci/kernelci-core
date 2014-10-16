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

"""Test common functions for all methods."""

import logging
import types
import unittest

from bson import tz_util

from datetime import (
    date,
    datetime,
    timedelta,
    time,
)

from mock import patch

from handlers.common import (
    calculate_date_range,
    get_aggregate_value,
    get_all_query_values,
    get_query_fields,
    get_query_sort,
    get_query_spec,
    get_skip_and_limit,
    get_and_add_date_range,
)


class TestHandlersCommon(unittest.TestCase):

    def setUp(self):
        super(TestHandlersCommon, self).setUp()

        logging.disable(logging.CRITICAL)

        self.min_time = time(tzinfo=tz_util.utc)
        patched_date = patch('handlers.common.date')
        self.mock_date = patched_date.start()

        self.addCleanup(patched_date.stop,)

    def tearDown(self):
        super(TestHandlersCommon, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_calculate_date_range_valid(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 17), self.min_time)
        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_zero(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2014, 1, 1), self.min_time)
        self.assertEqual(expected, calculate_date_range(0))

    def test_calculate_date_range_leap(self):
        self.mock_date.today.return_value = date(2012, 3, 14)

        expected = datetime.combine(date(2012, 2, 28), self.min_time)
        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_non_leap(self):
        self.mock_date.today.return_value = date(2013, 3, 14)

        expected = datetime.combine(date(2013, 2, 27), self.min_time)
        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_with_string(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, calculate_date_range('1'))

    def test_calculate_date_range_negative(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, calculate_date_range(-1))

    def test_calculate_date_range_negative_string(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, calculate_date_range('-1'))

    def test_calculate_date_range_out_of_range(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 27), self.min_time)
        self.assertEqual(
            expected,
            calculate_date_range(timedelta.max.days + 10)
        )

    def test_calculate_date_range_wrong_type(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 27), self.min_time)
        self.assertEqual(
            expected,
            calculate_date_range("15foo$%^%&^%&")
        )

    def test_get_aggregate_value_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_aggregate_value(query_args_func))

    def test_get_aggregate_value_valid(self):
        def query_args_func(key):
            if key == "aggregate":
                return ["foo"]
            else:
                return []

        self.assertEqual(get_aggregate_value(query_args_func), "foo")

    def test_get_aggregate_value_no_list(self):
        def query_args_func(key):
            return ""

        self.assertIsNone(get_aggregate_value(query_args_func))

    def test_get_aggregate_value_multi(self):
        def query_args_func(key):
            if key == "aggregate":
                return ["foo", "bar"]
            else:
                return []

        self.assertEqual(get_aggregate_value(query_args_func), "bar")

    def test_get_query_spec(self):
        valid_keys = ["a", "b", "c", "d"]

        def query_args_func(key):
            args = {
                "a": [1, 2],
                "b": [None, 3, None],
                "c": [None, None],
            }
            return args.get(key, [])

        expected = {"a": {"$in": [1, 2]}, "b": 3}
        self.assertEqual(expected, get_query_spec(query_args_func, valid_keys))

    def test_get_query_spec_raises(self):
        valid_keys = ["a", "b"]

        def query_args_func(key):
            args = {
                "a": 1
            }
            return args.get(key, [])

        self.assertRaises(
            TypeError, get_query_spec, query_args_func, valid_keys
        )

    def test_get_query_spec_wrong_keys_list(self):
        def query_args_func(self):
            return ""

        self.assertEqual({}, get_query_spec(query_args_func, []))
        self.assertEqual({}, get_query_spec(query_args_func, ()))
        self.assertEqual({}, get_query_spec(query_args_func, ""))

    def test_get_query_fields_valid_only_field(self):
        def query_args_func(key):
            args = {
                "field": ["a", "a", "b", "c"]
            }
            return args.get(key, [])

        self.assertIsInstance(
            get_query_fields(query_args_func), types.ListType
        )
        self.assertEqual(["a", "c", "b"], get_query_fields(query_args_func))

    def test_get_query_fields_valid_only_nfield(self):
        def query_args_func(key):
            args = {
                "nfield": ["a", "a", "b"]
            }
            return args.get(key, [])

        expected = {
            "a": False,
            "b": False
        }

        self.assertIsInstance(
            get_query_fields(query_args_func), types.DictionaryType
        )
        self.assertEqual(expected, get_query_fields(query_args_func))

    def test_get_query_fields_valid_both(self):
        def query_args_func(key):
            args = {
                "field": ["a", "b", "c"],
                "nfield": ["d", "d", "e"]
            }
            return args.get(key, [])

        expected = {
            "a": True,
            "b": True,
            "c": True,
            "d": False,
            "e": False
        }

        self.assertIsInstance(
            get_query_fields(query_args_func), types.DictionaryType
        )
        self.assertEqual(expected, get_query_fields(query_args_func))

    def test_get_query_fields_both_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_query_fields(query_args_func))

    def test_get_query_sort_empty(self):
        def query_args_func(key):
            return []

        self.assertIsNone(get_query_sort(query_args_func))

    def test_get_query_sort_not_sort(self):
        def query_args_func(key):
            args = {
                "sort_order": [1]
            }
            return args.get(key, [])

        self.assertIsNone(get_query_sort(query_args_func))

    def test_get_query_sort_wrong_order(self):
        def query_args_func(key):
            args = {
                "sort": ["foo"],
                "sort_order": [-10]
            }
            return args.get(key, [])

        expected = [("foo", -1)]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_query_sort_wrong_single_order(self):
        def query_args_func(key):
            args = {
                "sort": ["foo"],
                "sort_order": -10
            }
            return args.get(key, [])

        expected = [("foo", -1)]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_query_sort_multi_order(self):
        def query_args_func(key):
            args = {
                "sort": ["a", "b", "c"],
                "sort_order": [1, -1, 1]
            }
            return args.get(key, [])

        expected = [
            ("a", 1), ("b", 1), ("c", 1)
        ]

        self.assertEqual(expected, get_query_sort(query_args_func))

    def test_get_skip_and_limit_both_empty(self):
        def query_args_func(key):
            return []

        self.assertEqual((0, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_only_skip(self):
        def query_args_func(key):
            args = {
                "skip": [1]
            }
            return args.get(key, [])

        self.assertEqual((1, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_only_limit(self):
        def query_args_func(key):
            args = {
                "limit": [1]
            }
            return args.get(key, [])

        self.assertEqual((0, 1), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_not_list(self):
        def query_args_func(key):
            return 1

        self.assertEqual((0, 0), get_skip_and_limit(query_args_func))

    def test_get_skip_and_limit_valid(self):
        def query_args_func(key):
            args = {
                "limit": [0, 1, 2],
                "skip": [10, 20, 30]
            }
            return args.get(key, [])

            self.assertEqual((2, 30), get_skip_and_limit(query_args_func))

    def test_get_all_query_values(self):
        def query_args_func(key):
            args = {
                "skip": [10, 20, 30],
                "sort": ["job"],
            }
            return args.get(key, [])

        valid_keys = []

        return_value = get_all_query_values(query_args_func, valid_keys)
        self.assertEqual(len(return_value), 6)

    def test_get_and_add_date_range(self):
        def query_args_func(key):
            args = {
                "date_range": 1,
            }
            return args.get(key, [])

        spec = {}
        self.mock_date.today.return_value = date(2013, 3, 14)

        expected = {
            'created_on': {
                '$gte': datetime(
                    2013, 3, 13, 0, 0, tzinfo=tz_util.utc
                ),
                '$lt': datetime(
                    2013, 3, 14, 23, 59, 59, tzinfo=tz_util.utc
                )
            }
        }

        spec = get_and_add_date_range(spec, query_args_func)
        self.assertEqual(expected, spec)
