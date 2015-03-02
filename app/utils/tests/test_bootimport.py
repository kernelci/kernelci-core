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

import datetime
import json
import logging
import mongomock
import os
import sys
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
            lab_name="lab_name",
            kernel="kernel",
            job="job",
            defconfig="defconfig",
            arch="arm",
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
            uimage="uimage",
            uimage_addr="xip",
            mach="soc"
        )

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_parse_from_json_simple(self):
        doc = utils.bootimport._parse_boot_from_json(self.boot_report, self.db)

        self.assertIsInstance(doc, modb.BootDocument)
        self.assertEqual(doc.name, "board-job-kernel-defconfig-arm")
        self.assertEqual(doc.load_addr, "0x80200000")
        self.assertEqual(doc.endian, "little")
        self.assertEqual(doc.version, "1.0")
        self.assertEqual(doc.mach, "soc")
        self.assertEqual(doc.uimage, "uimage")
        self.assertIsInstance(doc.metadata, types.DictionaryType)

    def test_check_for_null_with_none(self):
        boot_report = (
            '{"job": null, "board": "board", '
            '"kernel": "kernel", "defconfig": "defconfig", "lab_name": "lab"}'
        )

        self.assertRaises(
            utils.bootimport.BootImportError,
            utils.bootimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_null(self):
        boot_report = (
            '{"job": "job", "board": "null", '
            '"kernel": "kernel", "defconfig": "defconfig", "lab_name": "lab"}'
        )

        self.assertRaises(
            utils.bootimport.BootImportError,
            utils.bootimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_none_string(self):
        boot_report = (
            '{"job": "job", "board": "board", '
            '"kernel": "None", "defconfig": "defconfig", "lab_name": "lab"}'
        )
        boot_json = json.loads(boot_report)

        self.assertRaises(
            utils.bootimport.BootImportError,
            utils.bootimport._check_for_null, boot_json, boot_json.get)

    def test_check_for_null_with_none_string_lower(self):
        boot_report = (
            '{"job": "job", "board": "board", '
            '"kernel": "kernel", "defconfig": "none", "lab_name": "lab"}'
        )
        boot_json = json.loads(boot_report)

        self.assertRaises(
            utils.bootimport.BootImportError,
            utils.bootimport._check_for_null, boot_json, boot_json.get)

    @patch("utils.db.get_db_connection")
    def test_import_and_save_boot(self, mock_db):
        mock_db = self.db

        code, doc_id = utils.bootimport.import_and_save_boot(
            self.boot_report, {}, base_path=self.base_path
        )
        lab_dir = os.path.join(
            self.base_path, "job", "kernel", "arm-defconfig", "lab_name"
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

    @patch("utils.bootimport._check_for_null")
    def test_parse_from_json_wrong_json(self, mock_null):
        boot_json = {
            "foo": "bar"
        }
        self.assertRaises(
            KeyError, utils.bootimport._parse_boot_from_json(boot_json, self.db)
        )

    def test_parse_from_json_with_null(self):
        boot_json = {
            "board": "null"
        }

        doc = utils.bootimport._parse_boot_from_json(boot_json, self.db)
        self.assertIsNone(doc)

    @patch("utils.bootimport._parse_boot_from_json")
    def test_import_and_save_no_doc(self, mock_parse):
        mock_parse.return_value = None

        code, doc_id = utils.bootimport.import_and_save_boot({}, {})
        self.assertIsNone(code)
        self.assertIsNone(doc_id)

    def test_parse_from_file_no_file(self):
        doc = utils.bootimport._parse_boot_from_file(None, self.db)
        self.assertIsNone(doc)

    def test_parse_from_file_wrong_file(self):
        doc = utils.bootimport._parse_boot_from_file('foobar.json', self.db)
        self.assertIsNone(doc)

    @patch("utils.bootimport._check_for_null")
    def test_parse_from_file_no_key(self, mock_null):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, suffix="json", delete=False
        )
        boot_obj = {
            "foo": "bar"
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertIsNone(doc)
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_wrong_boot_time_too_big(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, suffix="json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "boot_time": sys.maxint
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, "board")
            self.assertEqual(doc.job, "job")
            self.assertEqual(doc.kernel, "kernel")
            self.assertEqual(doc.defconfig, "defconfig")
            self.assertEqual(doc.dtb, "dtb")
            self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_wrong_boot_time_too_big_negative(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, suffix="json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "boot_time": -sys.maxint - 1
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, "board")
            self.assertEqual(doc.job, "job")
            self.assertEqual(doc.kernel, "kernel")
            self.assertEqual(doc.defconfig, "defconfig")
            self.assertEqual(doc.dtb, "dtb")
            self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_wrong_boot_time_negative(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, suffix="json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "boot_time": -1500.0
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, "board")
            self.assertEqual(doc.job, "job")
            self.assertEqual(doc.kernel, "kernel")
            self.assertEqual(doc.defconfig, "defconfig")
            self.assertEqual(doc.dtb, "dtb")
            self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_valid(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, suffix="json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "boot_time": 0,
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, "board")
            self.assertEqual(doc.job, "job")
            self.assertEqual(doc.kernel, "kernel")
            self.assertEqual(doc.defconfig, "defconfig")
            self.assertEqual(doc.dtb, "dtb")
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_no_board(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, prefix="boot-", suffix=".json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "dtb": "dtbs/board.dtb",
            "lab_name": "lab_name",
            "boot_time": 0,
        }

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, "board")
            self.assertEqual(doc.job, "job")
            self.assertEqual(doc.kernel, "kernel")
            self.assertEqual(doc.defconfig, "defconfig")
            self.assertEqual(doc.dtb, "dtbs/board.dtb")
        finally:
            os.remove(boot_log.name)

    def test_parse_from_file_no_board_tmp_dtb(self):
        boot_log = tempfile.NamedTemporaryFile(
            mode='w+b', bufsize=-1, prefix="boot-", suffix=".json", delete=False
        )
        boot_obj = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "dtb": "tmp/board.dtb",
            "lab_name": "lab_name",
            "boot_time": 0,
            "arch": "arm"
        }

        board = os.path.splitext(
            os.path.basename(boot_log.name).replace('boot-', ''))[0]

        try:
            with open(boot_log.name, mode="w") as boot_write:
                boot_write.write(json.dumps(boot_obj))

            doc = utils.bootimport._parse_boot_from_file(
                boot_log.name, self.db)

            self.assertEqual(doc.board, board)
            self.assertEqual(doc.dtb, "tmp/board.dtb")
        finally:
            os.remove(boot_log.name)
