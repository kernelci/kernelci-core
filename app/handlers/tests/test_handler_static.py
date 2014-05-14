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

"""Test static or class methods from handler classes."""

import unittest

from bson import tz_util

from datetime import (
    date,
    datetime,
    timedelta,
    time,
)

from mock import patch

from handlers.base import BaseHandler


class TestHandlerStatic(unittest.TestCase):

    def setUp(self):
        super(TestHandlerStatic, self).setUp()

        self.min_time = time(tzinfo=tz_util.utc)
        patched_date = patch('handlers.base.date')
        self.mock_date = patched_date.start()

        self.addCleanup(patched_date.stop,)

    def test_calculate_date_range_valid(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 17), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range(15))

    def test_calculate_date_range_zero(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2014, 1, 1), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range(0))

    def test_calculate_date_range_leap(self):
        self.mock_date.today.return_value = date(2012, 3, 14)

        expected = datetime.combine(date(2012, 2, 28), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range(15))

    def test_calculate_date_range_non_leap(self):
        self.mock_date.today.return_value = date(2013, 3, 14)

        expected = datetime.combine(date(2013, 2, 27), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range(15))

    def test_calculate_date_range_with_string(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range('1'))

    def test_calculate_date_range_negative(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range(-1))

    def test_calculate_date_range_negative_string(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 31), self.min_time)
        self.assertEqual(expected, BaseHandler._calculate_date_range('-1'))

    def test_calculate_date_range_out_of_range(self):
        self.mock_date.today.return_value = date(2014, 1, 1)

        expected = datetime.combine(date(2013, 12, 17), self.min_time)
        self.assertEqual(
            expected,
            BaseHandler._calculate_date_range(timedelta.max.days + 10)
        )
