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
import tempfile
import types
import unittest

from mock import patch

import models.boot as modb
import utils.bootimport


class TestParseBoot(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')
        self.base_path = tempfile.gettempdir()

        self.boot_report = dict(
            version="1.0",
            board="board",
            lab_id="lab_id",
            kernel="kernel",
            job="job",
            defconfig="defconfig",
            boot_log='boot-board-name.log',
            boot_result="PASS",
            boot_result_description="passed",
            boot_time=28.07,
            boot_warnings=0,
            dtb="dtb/board-name.dtb",
            dtb_addr="0x81f00000",
            initrd_addr="0x81f00001",
            kernel_image="zImage",
            loadaddr="0x80200000",
            endian="little",
            uImage=True,
            uimage_addr="xip"
        )

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_parse_from_json_simple(self):
        doc = utils.bootimport._parse_boot_from_json(self.boot_report)

        self.assertIsInstance(doc, modb.BootDocument)
        self.assertEqual(doc.name, "board-job-kernel-defconfig")
        self.assertEqual(doc.load_addr, "0x80200000")
        self.assertEqual(doc.endianness, "little")
        self.assertEqual(doc.version, "1.0")
        self.assertIsInstance(doc.metadata, types.DictionaryType)

    @patch("utils.db.get_db_connection")
    def test_import_and_save_boot(self, mock_db):
        mock_db = self.db

        code, doc_id = utils.bootimport.import_and_save_boot(
            self.boot_report, {}, base_path=self.base_path
        )
        lab_dir = os.path.join(
            self.base_path, "job", "kernel", "defconfig", "lab_id"
        )
        boot_file = os.path.join(lab_dir, "boot-board.json")

        self.assertTrue(os.path.isdir(lab_dir))
        self.assertTrue(os.path.isfile(boot_file))
        self.assertEqual(code, 201)

        try:
            os.remove(boot_file)
            os.rmdir(lab_dir)
        except OSError:
            pass

    def test_parse_from_json_wrong_json(self):
        boot_json = {
            "foo": "bar"
        }
        self.assertRaises(
            KeyError, utils.bootimport._parse_boot_from_json(boot_json)
        )

    @patch("utils.bootimport._parse_boot_from_json")
    def test_import_and_save_no_doc(self, mock_parse):
        mock_parse.return_value = None

        code, doc_id = utils.bootimport.import_and_save_boot({}, {})
        self.assertIsNone(code)
        self.assertIsNone(doc_id)
