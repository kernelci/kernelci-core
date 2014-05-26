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
import logging
import mongomock
import os
import tempfile
import unittest

from mock import patch, MagicMock, Mock

from datetime import (
    datetime,
    timedelta,
)

from models.boot import BootDocument
from utils.bootimport import (
    _parse_boot_log,
    parse_boot_from_json,
)


class TestParseBoot(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')

        self.boot_report = dict(
            boot_log='boot-board-name.log',
            boot_result='PASS',
            boot_time=28.07,
            boot_warnings=0,
            dtb='dtb/dir',
            dtb_addr='0x81f00000',
            initr_addr='0x81f00001',
            kernel_image='zImage',
            loadaddr='0x80200000',
        )

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_parse_boot_log(self):
        temp_json_f = os.path.join(
            tempfile.gettempdir(), 'boot-board-name.json'
        )

        try:
            with open(temp_json_f, 'w') as w_f:
                w_f.write(json.dumps(self.boot_report))

            doc = _parse_boot_log(temp_json_f, 'job', 'kernel', 'defconfig')

            time_d = timedelta(seconds=28.07)
            boot_time = datetime(
                1970, 1, 1,
                minute=time_d.seconds / 60,
                second=time_d.seconds % 60,
                microsecond=time_d.microseconds
            )

            self.assertIsInstance(doc, BootDocument)
            self.assertEqual(doc.board, 'board-name')
            self.assertEqual(doc.job, 'job')
            self.assertEqual(doc.kernel, 'kernel')
            self.assertEqual(doc.defconfig, 'defconfig')
            self.assertIsInstance(doc.time, datetime)
            self.assertEqual(doc.time, boot_time)
            self.assertEqual(doc.boot_log, 'boot-board-name.log')
            self.assertEqual(doc.status, 'PASS')
            self.assertEqual(doc.load_addr, '0x80200000')
        finally:
            os.unlink(temp_json_f)

    @patch('utils.bootimport._parse_boot_log')
    @patch('os.path.isfile')
    @patch('glob.iglob', new=Mock(return_value=['boot-board.json']))
    @patch('os.path.isdir')
    @patch('os.listdir')
    def test_parse_from_json_simple(
            self, mock_listdir, mock_isdir, mock_isfile, mock_parse):
        json_obj = dict(job='job', kernel='kernel')

        mock_isfile.return_value = True
        mock_isdir.return_value = True
        mock_parse.side_effect = [MagicMock(), MagicMock()]
        mock_listdir.return_value = ('.hidden', 'defconfdir')

        docs = parse_boot_from_json(json_obj, base_path=tempfile.gettempdir())

        self.assertEqual(len(docs), 1)
