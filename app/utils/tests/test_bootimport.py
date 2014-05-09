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

import logging
import mongomock
import os
import types
import unittest

from datetime import (
    datetime,
    timedelta,
)

from models.boot import BootDocument
from utils.bootimport import (
    _parse_boot_log
)


class TestParseBoot(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')

        self.sample_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'samples'))
        self.simple_boot_log = os.path.join(
            self.sample_dir, 'sample_boot_simple.log')
        self.complex_boot_log = os.path.join(
            self.sample_dir, 'sample_boot_complex.log')

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_import_parse_simple(self):
        docs = _parse_boot_log(self.simple_boot_log)

        self.assertEqual(len(docs), 1)
        self.assertIsInstance(docs[0], BootDocument)

        self.assertEqual(
            docs[0].name, 'boot-next-next-20140505-arm-davinci_all_defconfig')

        self.assertIsInstance(docs[0].boards, types.ListType)
        self.assertEqual(len(docs[0].boards), 2)

        self.assertEqual(docs[0].job, 'next')
        self.assertEqual(docs[0].kernel, 'next-20140505')
        self.assertEqual(docs[0].defconfig, 'arm-davinci_all_defconfig')
        self.assertIsInstance(docs[0].created, datetime)

        self.assertIsInstance(docs[0].boards[0], types.DictionaryType)
        self.assertEqual(docs[0].boards[0]['board'], 'legacy,dm365evm')

        self.assertIsInstance(docs[0].boards[0]['time'], datetime)

        time_d = timedelta(minutes=0, seconds=17.7)
        time = datetime(
            1970, 1, 1,
            minute=time_d.seconds / 60,
            second=time_d.seconds % 60,
            microsecond=time_d.microseconds
        )

        self.assertEqual(docs[0].boards[0]['time'], time)
        self.assertEqual(docs[0].boards[0]['warnings'], '1')

    def test_import_parse_complex(self):
        docs = _parse_boot_log(self.complex_boot_log)

        self.assertEqual(len(docs), 11)
