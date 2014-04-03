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

import mongomock
import unittest

from mock import patch

from models import DB_NAME
from utils.subscription import subscribe


class TestSubscription(unittest.TestCase):

    def setUp(self):
        self.database = mongomock.Database(mongomock.Connection(), DB_NAME)

    @patch("utils.subscription.find_one")
    def test_subscribe_email_no_job(self, mock_find_one):

        mock_find_one.side_effect = [None]
        json_obj = dict(
            job='job',
            email='email'
        )

        result = subscribe(json_obj, self.database)
        self.assertEqual(result, 404)

    @patch("utils.subscription.find_one")
    def test_subscribe_email_valid_job(self, mock_find_one):

        mock_find_one.side_effect = [
            dict(_id='job'),
            None,
        ]
        json_obj = dict(
            job='job',
            email='email'
        )

        result = subscribe(json_obj, self.database)
        self.assertEqual(result, 201)
