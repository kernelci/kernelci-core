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

from bson.json_util import dumps
from mock import (
    MagicMock,
    patch,
)

from handlers import DefConfHandler
from models import DB_NAME
from models.defconfig import DEFCONFIG_COLLECTION


class TestDefConfHandler(unittest.TestCase):

    def setUp(self):
        self.application = MagicMock()
        self.request = MagicMock()

        self.handler = DefConfHandler(self.application, self.request)
        self.handler.write = MagicMock()

        super(TestDefConfHandler, self).setUp()

    @patch("handlers.DefConfHandler.db")
    @patch("handlers.DefConfHandler.collection")
    def job_handler_get_multiple_result(self, mock_coll, mock_db):
        expcted = [
            {"_id": "defconf1", "job_id": "job1"},
            {"_id": "defconf0", "job_id": "job0"}
        ]

        self.handler.db = mongomock.Database(mongomock.Connection(), DB_NAME)
        self.handler.collection = mongomock.Collection(
            self.handler.db, DEFCONFIG_COLLECTION)

        self.handler.collection.insert(dict(_id="defconf0", job_id="job0"))
        self.handler.collection.insert(dict(_id="defconf1", job_id="job1"))

        self.handler.get()
        args, _ = self.handler.write.call_args
        self.assertEqual(args[0], dumps(expcted))

    @patch("handlers.DefConfHandler.db")
    @patch("handlers.DefConfHandler.collection")
    def job_handler_get_one_result(self, mock_coll, mock_db):
        expected = {"_id": "defconf2", "job_id": "job2"}

        self.handler.db = mongomock.Database(mongomock.Connection(), DB_NAME)
        self.handler.collection = mongomock.Collection(
            self.handler.db, DEFCONFIG_COLLECTION)

        self.handler.collection.insert(dict(_id="defconf0", job_id="job0"))
        self.handler.collection.insert(dict(_id="defconf1", job_id="job1"))
        self.handler.collection.insert(dict(_id="defconf2", job_id="job2"))
        self.handler.collection.insert(dict(_id="defconf3", job_id="job3"))

        kwargs = {"id": "defconf2"}

        self.handler.get(**kwargs)
        args, _ = self.handler.write.call_args
        self.assertEqual(args[0], dumps(expected))
