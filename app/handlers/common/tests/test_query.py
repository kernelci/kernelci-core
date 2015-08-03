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

"""Test handler query args functions."""

import datetime
import logging
import mock
import types
import unittest

from bson import (
    objectid,
    tz_util
)

from handlers.common.query import (
    _valid_value,
    add_created_on_date,
    calculate_date_range,
    get_aggregate_value,
    get_all_query_values,
    get_and_add_date_range,
    get_and_add_gte_lt_keys,
    get_and_add_time_range,
    get_compared_value,
    get_created_on_date,
    get_query_fields,
    get_query_sort,
    get_query_spec,
    get_skip_and_limit,
    get_trigger_query_values,
    update_id_fields
)


class TestCommonQuery(unittest.TestCase):

    def setUp(self):
        super(TestCommonQuery, self).setUp()
        logging.disable(logging.CRITICAL)
        self.min_time = datetime.time(tzinfo=tz_util.utc)

    def tearDown(self):
        super(TestCommonQuery, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_valid_values(self):
        self.assertFalse(_valid_value(""))
        self.assertFalse(_valid_value(u""))
        self.assertFalse(_valid_value([]))
        self.assertFalse(_valid_value(()))
        self.assertFalse(_valid_value(None))

        self.assertTrue(_valid_value(0))
        self.assertTrue(_valid_value(False))
        self.assertTrue(_valid_value(["foo", "bar"]))
        self.assertTrue(_valid_value(("foo", "bar")))

    def test_update_id_fields(self):
        spec = {
            "job_id": "123344567",
            "_id": "0123456789ab0123456789ab",
            "foo": 1234,
            "build_id": "0123456789ab0123456789ab"
        }
        update_id_fields(spec)
        expected = {
            "_id": objectid.ObjectId("0123456789ab0123456789ab"),
            "foo": 1234,
            "build_id": objectid.ObjectId("0123456789ab0123456789ab")
        }

        self.assertDictEqual(expected, spec)

    def test_calculate_date_range_valid(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 17), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_zero(self):
        expected = datetime.datetime.combine(
            datetime.date(2014, 1, 1), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(0))

    def test_calculate_date_range_leap(self):
        expected = datetime.datetime.combine(
            datetime.date(2012, 2, 28), self.min_time)
        start_value = datetime.date(2012, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_non_leap(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 2, 27), self.min_time)
        start_value = datetime.date(2013, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(15))

    def test_calculate_date_range_with_string(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range("1"))

    def test_calculate_date_range_negative(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range(-1))

    def test_calculate_date_range_negative_string(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 31), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(expected, calculate_date_range("-1"))

    def test_calculate_date_range_out_of_range(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 27), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        self.assertEqual(
            expected,
            calculate_date_range(datetime.timedelta.max.days + 10)
        )

    def test_calculate_date_range_wrong_type(self):
        expected = datetime.datetime.combine(
            datetime.date(2013, 12, 27), self.min_time)
        start_value = datetime.date(2014, 1, 1)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

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

    @mock.patch("handlers.common.query.KEY_TYPES", spec=True)
    def test_get_query_spec_with_tuple(self, mock_types):
        valid_keys = ["a", "b", "d"]

        mock_types.get = mock.Mock()
        mock_types.get.side_effect = [None, "int", "int"]

        def query_args_func(key):
            args = {
                "a": ["a"],
                "b": ["0", "1", "2"],
                "d": ["1"]
            }
            return args.get(key, [])

        expected = {"a": "a", "b": {"$in": [0, 1, 2]}, "d": 1}
        self.assertDictEqual(
            expected, get_query_spec(query_args_func, valid_keys))

    @mock.patch("handlers.common.query.KEY_TYPES", spec=True)
    def test_get_query_spec_with_tuple_invalid(self, mock_types):
        valid_keys = ["a", "b", "c", "d"]

        mock_types.get = mock.Mock()
        mock_types.get.side_effect = [None, "int", "int", "int"]

        def query_args_func(key):
            args = {
                "a": ["a"],
                "b": ["a", "1", "c"],
                "d": ["1", "2", "3", "bar"],
                "c": ["foo"]
            }
            return args.get(key, [])

        expected = {"a": "a"}
        self.assertDictEqual(
            expected, get_query_spec(query_args_func, valid_keys))

    def test_get_query_spec(self):
        valid_keys = ["a", "b", "c", "d"]

        def query_args_func(key):
            args = {
                "a": [0, 1, 2],
                "b": [None, 3, None],
                "c": [None, None, ""],
                "d": [False]
            }
            return args.get(key, [])

        expected = {"a": {"$in": [0, 1, 2]}, "b": 3, "d": False}
        self.assertDictEqual(
            expected, get_query_spec(query_args_func, valid_keys))

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

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2013, 3, 13, 0, 0, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2013, 3, 14, 23, 59, 59, tzinfo=tz_util.utc
                )
            }
        }

        start_value = datetime.date(2013, 3, 14)

        patcher = mock.patch("datetime.date", spec=True)
        patched_date = patcher.start()
        patched_date.today.return_value = start_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_date_range(spec, query_args_func)
        self.assertEqual(expected, spec)

    def test_get_and_add_date_range_with_created_on(self):
        def query_args_func(key):
            args = {
                "date_range": 1,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2014, 12, 7, 0, 0, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2014, 12, 8, 23, 59, 59, tzinfo=tz_util.utc
                )
            }
        }

        created_on = datetime.date(2014, 12, 8)

        spec = {}

        get_and_add_date_range(spec, query_args_func, created_on)
        self.assertEqual(expected, spec)

    def test_get_and_add_time_range(self):
        def query_args_func(key):
            args = {
                "time_range": 10,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 12, 25, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_no_value(self):
        def query_args_func(key):
            return []

        expected = {}
        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_negative_value(self):
        def query_args_func(key):
            args = {
                "time_range": -30,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 12, 5, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_too_big(self):
        def query_args_func(key):
            args = {
                "time_range": 60 * 24 * 2,
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 12, 12, 35, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_list(self):
        def query_args_func(key):
            args = {
                "time_range": [40, 10, 45],
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 11, 50, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_less_than_min(self):
        def query_args_func(key):
            args = {
                "time_range": 5
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 12, 25, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_with_string(self):
        def query_args_func(key):
            args = {
                "time_range": "5"
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 12, 25, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_and_add_time_range_with_string_with_error(self):
        def query_args_func(key):
            args = {
                "time_range": "foo"
            }
            return args.get(key, [])

        expected = {
            "created_on": {
                "$gte": datetime.datetime(
                    2015, 7, 13, 11, 35, 00, tzinfo=tz_util.utc
                ),
                "$lt": datetime.datetime(
                    2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc
                )
            }
        }

        now_value = datetime.datetime(
            2015, 7, 13, 12, 35, 00, tzinfo=tz_util.utc)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_date = patcher.start()
        patched_date.now.return_value = now_value
        self.addCleanup(patcher.stop)

        spec = {}

        get_and_add_time_range(spec, query_args_func)
        self.assertDictEqual(expected, spec)

    def test_get_created_on_date_missing(self):
        def query_args_func(key):
            args = {}
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_wrong_type(self):
        def query_args_func(key):
            args = {
                "created_on": 2014
            }
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_valid_format_1(self):
        def query_args_func(key):
            args = {
                "created_on": "2014-12-12"
            }
            return args.get(key, [])

        expected = datetime.date(2014, 12, 12)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_date_valid_format_2(self):
        def query_args_func(key):
            args = {
                "created_on": "20141212"
            }
            return args.get(key, [])

        expected = datetime.date(2014, 12, 12)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_date_wrong_format(self):
        def query_args_func(key):
            args = {
                "created_on": "201412121243"
            }
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_get_created_on_date_multiple(self):
        def query_args_func(key):
            args = {
                "created_on": ["20141211", "20141110"]
            }
            return args.get(key, [])

        expected = datetime.date(2014, 11, 10)
        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_raise_attribute_error_valid(self):
        a_date = datetime.datetime.strptime("2015-07-02", "%Y-%m-%d")
        expected = datetime.date(2015, 07, 02)

        patcher = mock.patch("datetime.datetime", spec=True)
        patched_datetime = patcher.start()
        self.addCleanup(patcher.stop)

        patched_datetime.strptime.side_effect = [
            AttributeError("Attribute error"), a_date]

        def query_args_func(key):
            args = {
                "created_on": "2015-07-02"
            }
            return args.get(key, [])

        self.assertEqual(expected, get_created_on_date(query_args_func))

    def test_get_created_on_raise_attribute_error_not_valid(self):
        patcher = mock.patch("datetime.datetime", spec=True)
        patched_datetime = patcher.start()
        self.addCleanup(patcher.stop)

        patched_datetime.strptime.side_effect = AttributeError(
            "Attribute error")

        def query_args_func(key):
            args = {
                "created_on": "2015-07-02"
            }
            return args.get(key, [])

        self.assertIsNone(get_created_on_date(query_args_func))

    def test_add_created_on_date_valid(self):
        created_on = datetime.date(2014, 12, 11)
        spec = {"foo": "bar"}

        expected = {
            "foo": "bar",
            "created_on": {
                "$gte": datetime.datetime(
                    2014, 12, 11, 0, 0, tzinfo=tz_util.utc),
                "$lt": datetime.datetime(
                    2014, 12, 11, 23, 59, 59, tzinfo=tz_util.utc)
            }
        }

        add_created_on_date(spec, created_on)
        self.assertDictEqual(expected, spec)

    def test_add_created_on_date_wrong(self):
        spec = {"foo": "bar", "created_on": "foo"}
        expected = {"foo": "bar"}

        add_created_on_date(spec, None)
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, 12345)
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, {})
        self.assertDictEqual(expected, spec)

        add_created_on_date(spec, [1234])
        self.assertDictEqual(expected, spec)

    @mock.patch("handlers.common.query.KEY_TYPES", spec=True)
    def test_get_gte_lt_simple(self, mock_types):
        valid_keys = ["a", "b"]
        spec = {}

        mock_types.get = mock.Mock()
        mock_types.get.side_effect = ["int", "int", "int"]

        def query_args_func(key):
            args = {
                "gte": "a,1",
                "lt": "a,2",
            }
            return args.get(key, [])

        expected = {
            "a": {
                "$gte": 1, "$lt": 2
            }
        }

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_gte_lt_simple_different(self):
        def query_args_func(key):
            args = {
                "gte": "a,1",
                "lt": "b,2"
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]
        expected = {
            "a": {"$gte": "1"},
            "b": {"$lt": "2"}
        }

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_gte_lt_simple_with_null_and_exc(self):
        def query_args_func(key):
            args = {
                "gte": "a,",
                "lt": "b"
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual({}, spec)

    def test_get_gte_lt_simple_without_gte(self):
        def query_args_func(key):
            args = {
                "lt": "b,3"
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]
        expected = {"b": {"$lt": "3"}}

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_gte_lt_simple_without_lt(self):
        def query_args_func(key):
            args = {
                "gte": "b,3"
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]
        expected = {"b": {"$gte": "3"}}

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_gte_lt_list(self):
        def query_args_func(key):
            args = {
                "gte": ["b,3", "a,4"],
                "lt": ["b,6", "a,10", "c,9"]
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]
        expected = {
            "b": {"$gte": "3", "$lt": "6"},
            "a": {"$gte": "4", "$lt": "10"}
        }

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    @mock.patch("handlers.common.query.KEY_TYPES", spec=True)
    def test_get_gte_lt_list_wrong(self, mock_types):
        spec = {}
        valid_keys = ["a", "b", "c"]

        mock_types.get = mock.Mock()
        mock_types.get.side_effect = ["int", "int", "int", "int", "int"]

        def query_args_func(key):
            args = {
                "gte": ["b,0", "a,4"],
                "lt": ["b,6", "a,10", "c,foo"]
            }
            return args.get(key, [])

        expected = {
            "b": {"$gte": 0, "$lt": 6},
            "a": {"$gte": 4, "$lt": 10}
        }

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_gte_lt_list_without_lt(self):
        def query_args_func(key):
            args = {
                "gte": ["b,3", "a,4"]
            }
            return args.get(key, [])

        spec = {}
        valid_keys = ["a", "b"]
        expected = {"b": {"$gte": "3"}, "a": {"$gte": "4"}}

        get_and_add_gte_lt_keys(spec, query_args_func, valid_keys)
        self.assertDictEqual(expected, spec)

    def test_get_all_trigger_query_values(self):
        def query_args_func(key):
            args = {
                "skip": 10,
                "limit": 100,
            }
            return args.get(key, [])

        valid_keys = []

        return_value = get_trigger_query_values(query_args_func, valid_keys)
        self.assertEqual(len(return_value), 6)

    def test_get_compared_key_no_key(self):
        def query_args_func(key):
            return None
        compared = get_compared_value(query_args_func)
        self.assertFalse(compared)

    def test_get_compared_key_no_key_list(self):
        def query_args_func(key):
            return []
        compared = get_compared_value(query_args_func)
        self.assertFalse(compared)

    def test_get_compared_key_with_key_list(self):
        def query_args_func(key):
            return [1, 2, 0]
        compared = get_compared_value(query_args_func)
        self.assertFalse(compared)

    def test_get_compared_key_with_key(self):
        def query_args_func(key):
            args = {
                "compared": 1
            }
            return args.get(key, [])

        compared = get_compared_value(query_args_func)
        self.assertTrue(compared)

    def test_get_compared_key_with_key_string(self):
        def query_args_func(key):
            args = {
                "compared": "1"
            }
            return args.get(key, [])

        compared = get_compared_value(query_args_func)
        self.assertTrue(compared)
