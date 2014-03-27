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

from handlers import JobHandler
from models import (
    DB_NAME,
    JOB_COLLECTION
)


class TestJobHandler(unittest.TestCase):

    def setUp(self):
        self.application = MagicMock()
        self.request = MagicMock()

        self.handler = JobHandler(self.application, self.request)
        self.handler.write = MagicMock()

        super(TestJobHandler, self).setUp()

    @patch("handlers.JobHandler.db")
    @patch("handlers.JobHandler.collection")
    def job_handler_get_multiple_result(self, mock_coll, mock_db):
        expcted = [
            {"_id": "job1"},
            {"_id": "job0"}
        ]

        self.handler.db = mongomock.Database(mongomock.Connection(), DB_NAME)
        self.handler.collection = mongomock.Collection(
            self.handler.db, JOB_COLLECTION)

        self.handler.collection.insert(dict(_id="job0"))
        self.handler.collection.insert(dict(_id="job1"))

        self.handler.get()
        args, _ = self.handler.write.call_args
        self.assertEqual(args[0], dumps(expcted))

    @patch("handlers.JobHandler.db")
    @patch("handlers.JobHandler.collection")
    def job_handler_get_one_result(self, mock_coll, mock_db):
        expected = {"_id": "job2"}

        self.handler.db = mongomock.Database(mongomock.Connection(), DB_NAME)
        self.handler.collection = mongomock.Collection(
            self.handler.db, JOB_COLLECTION)

        self.handler.collection.insert(dict(_id="job0"))
        self.handler.collection.insert(dict(_id="job1"))
        self.handler.collection.insert(dict(_id="job2"))
        self.handler.collection.insert(dict(_id="job3"))

        kwargs = {"id": "job2"}

        self.handler.get(**kwargs)
        args, _ = self.handler.write.call_args
        self.assertEqual(args[0], dumps(expected))
