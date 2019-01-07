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
import errno
import json
import logging
import mock
import mongomock
import os
import pymongo
import shutil
import sys
import tempfile
import types
import unittest

import models.boot as mboot
import utils.boot as bimport
import utils.errors


class TestParseBoot(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")
        self.base_path = tempfile.gettempdir()

        self.boot_report = dict(
            version="1.1",
            board="board",
            lab_name="lab_name",
            kernel="kernel",
            job="job",
            defconfig="defconfig",
            arch="arm",
            boot_log="boot-board-name.log",
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
            mach="soc",
            bootloader="bootloader",
            bootloader_version="1.2.3",
            chainloader="chainloader",
            filesystem="nfs",
            boot_job_id="1234",
            boot_job_url="http://boot-executor.example.net",
            git_branch="branch"
        )

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @mock.patch("utils.db.get_db_connection")
    def test_import_and_save_db_error(self, mock_db):
        mock_db.side_effect = pymongo.errors.ConnectionFailure("ConnErr")

        self.assertRaises(
            utils.errors.BackendError,
            bimport.import_and_save_boot, self.boot_report, {})

    def test_parse_from_json_simple(self):
        errors = {}
        doc = bimport._parse_boot_from_json(self.boot_report, self.db, errors)

        self.assertIsInstance(doc, mboot.BootDocument)
        self.assertEqual(doc.load_addr, "0x80200000")
        self.assertEqual(doc.endian, "little")
        self.assertEqual(doc.version, "1.1")
        self.assertEqual(doc.mach, "soc")
        self.assertEqual(doc.uimage, "uimage")
        self.assertEqual(doc.bootloader, "bootloader")
        self.assertEqual(doc.bootloader_version, "1.2.3")
        self.assertEqual(doc.chainloader, "chainloader")
        self.assertEqual(doc.filesystem, "nfs")
        self.assertEqual(doc.boot_job_id, "1234")
        self.assertIsInstance(doc.metadata, types.DictionaryType)

    def test_check_for_null_with_none(self):
        boot_report = {
            "job": None,
            "board": None,
            "kernel": None,
            "defconfig": None,
            "lab_name": None,
            "git_branch": None
        }

        self.assertRaises(
            bimport.BootValidationError, bimport._check_for_null, boot_report)

    def test_check_for_null_with_null_from_string(self):
        boot_report = (
            '{"job": "Null", "board": "Null", "git_branch": "Null", '
            '"kernel": "Null", "defconfig": "Null", "lab_name": "Null"}'
        )

        self.assertRaises(
            bimport.BootValidationError,
            bimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_null_from_string_lower(self):
        boot_report = (
            '{"job": "null", "board": "null", "git_branch": "null", '
            '"kernel": "null", "defconfig": "null", "lab_name": "null"}'
        )

        self.assertRaises(
            bimport.BootValidationError,
            bimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_none_from_string(self):
        boot_report = (
            '{"job": "None", "board": "None", "git_branch": "None", '
            '"kernel": "None", "defconfig": "None", "lab_name": "None"}'
        )

        self.assertRaises(
            bimport.BootValidationError,
            bimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_none_from_string_lower(self):
        boot_report = (
            '{"job": "none", "board": "none", "git_branch": "none", '
            '"kernel": "none", "defconfig": "none", "lab_name": "none"}'
        )

        self.assertRaises(
            bimport.BootValidationError,
            bimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_empty_string_from_string(self):
        boot_report = (
            '{"job": "", "board": "", "git_branch": "", '
            '"kernel": "", "defconfig": "", "lab_name": ""}'
        )

        self.assertRaises(
            bimport.BootValidationError,
            bimport._check_for_null, json.loads(boot_report))

    def test_check_for_null_with_empty_string(self):
        boot_report = {
            "job": "",
            "board": "",
            "kernel": "",
            "defconfig": "",
            "lab_name": "",
            "git_branch": ""
        }

        self.assertRaises(
            bimport.BootValidationError, bimport._check_for_null, boot_report)

    def test_save_to_disk(self):
        errors = {}
        base_path = tempfile.mkdtemp()
        json_obj = {
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "arch": "arm",
            "defconfig_full": "defconfig+FRAGMENT",
            "lab_name": "lab",
            "git_branch": "branch"
        }
        boot_doc = mboot.BootDocument(
            "board", "job", "kernel", "defconfig", "lab", "branch",
            "defconfig+FRAGMENT", "arm")
        expected_path = os.path.join(
            base_path,
            "job", "branch", "kernel", "arm", "defconfig+FRAGMENT", "lab")
        expected_file = os.path.join(expected_path, "boot-board.json")
        try:
            bimport.save_to_disk(boot_doc, json_obj, base_path, errors)
            self.assertTrue(os.path.isdir(expected_path))
            self.assertTrue(os.path.exists(expected_file))
            self.assertDictEqual({}, errors,)
        finally:
            shutil.rmtree(base_path)

    def test_save_to_disk_dir_exists(self):
        errors = {}
        base_path = tempfile.mkdtemp()
        json_obj = {
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "arch": "arm",
            "defconfig_full": "defconfig+FRAGMENT",
            "git_branch": "branch",
            "lab_name": "lab"
        }
        boot_doc = mboot.BootDocument(
            "board", "job", "kernel", "defconfig", "lab", "branch",
            "defconfig+FRAGMENT", "arm")
        expected_path = os.path.join(
            base_path,
            "job", "branch", "kernel", "arm", "defconfig+FRAGMENT", "lab")
        expected_file = os.path.join(expected_path, "boot-board.json")
        try:
            os.makedirs(expected_path)
            self.assertTrue(os.path.isdir(expected_path))

            patcher = mock.patch("os.path.isdir", spec=True)
            patched_dir = patcher.start()
            patched_dir.return_value = False
            self.addCleanup(patcher.stop)

            bimport.save_to_disk(boot_doc, json_obj, base_path, errors)
            self.assertTrue(os.path.exists(expected_file))
            self.assertDictEqual({}, errors)
        finally:
            shutil.rmtree(base_path)

    @mock.patch("os.makedirs")
    def test_save_to_disk_dir_create_error(self, mock_mkdir):
        errors = {}
        base_path = tempfile.mkdtemp()
        json_obj = {
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "arch": "arm",
            "defconfig_full": "defconfig+FRAGMENT",
            "lab_name": "lab",
            "git_branch": "branch"
        }
        boot_doc = mboot.BootDocument(
            "board", "job", "kernel", "defconfig", "lab", "branch",
            "defconfig+FRAGMENT", "arm")
        expected_path = os.path.join(
            base_path,
            "job", "branch", "kernel", "arm", "defconfig+FRAGMENT", "lab")
        expected_file = os.path.join(expected_path, "boot-board.json")

        exception = OSError("Error")
        exception.errno = errno.EIO
        mock_mkdir.side_effect = exception

        try:
            bimport.save_to_disk(boot_doc, json_obj, base_path, errors)
            self.assertFalse(os.path.exists(expected_path))
            self.assertFalse(os.path.exists(expected_file))
            self.assertListEqual([500], errors.keys())
        finally:
            shutil.rmtree(base_path)

    @mock.patch("utils.db.get_db_connection")
    def test_import_and_save_boot(self, mock_db):
        mock_db = self.db

        bimport.import_and_save_boot(
            self.boot_report, {}, base_path=self.base_path)
        lab_dir = os.path.join(
            self.base_path,
            "job", "branch", "kernel", "arm", "defconfig", "lab_name")
        boot_file = os.path.join(lab_dir, "boot-board.json")

        self.assertTrue(os.path.isdir(lab_dir))
        self.assertTrue(os.path.isfile(boot_file))

        try:
            os.remove(boot_file)
            os.rmdir(lab_dir)
        except OSError:
            pass

    @mock.patch("utils.boot._check_for_null")
    def test_parse_from_json_wrong_json(self, mock_null):
        boot_json = {
            "foo": "bar"
        }
        errors = {}
        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)
        self.assertIsNone(doc)
        self.assertListEqual([400], errors.keys())

    def test_parse_from_json_with_null(self):
        boot_json = {
            "board": "null"
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)
        self.assertIsNone(doc)
        self.assertListEqual([400], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    @mock.patch("utils.boot._parse_boot_from_json")
    def test_import_and_save_no_doc(self, mock_parse, mock_db):
        mock_parse.return_value = None
        mock_db = self.db

        doc_id = bimport.import_and_save_boot({}, {})
        self.assertIsNone(doc_id)

    def test_parse_from_json_no_json(self):
        errors = {}
        doc = bimport._parse_boot_from_json(None, self.db, errors)
        self.assertIsNone(doc)
        self.assertDictEqual({}, errors)

    def test_parse_from_json_wrong_boot_time_too_big(self):
        boot_json = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "boot_time": sys.maxint
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)

        self.assertEqual(doc.board, "board")
        self.assertEqual(doc.job, "job")
        self.assertEqual(doc.kernel, "kernel")
        self.assertEqual(doc.defconfig, "defconfig")
        self.assertEqual(doc.dtb, "dtb")
        self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        self.assertListEqual([400], errors.keys())

    def test_parse_from_json_wrong_boot_time_too_big_negative(self):
        boot_json = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "boot_time": -sys.maxint - 1
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)

        self.assertEqual(doc.board, "board")
        self.assertEqual(doc.job, "job")
        self.assertEqual(doc.kernel, "kernel")
        self.assertEqual(doc.defconfig, "defconfig")
        self.assertEqual(doc.dtb, "dtb")
        self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        self.assertListEqual([400], errors.keys())

    def test_parse_from_json_wrong_boot_time_negative(self):
        boot_json = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "boot_time": -1500.0
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)

        self.assertEqual(doc.board, "board")
        self.assertEqual(doc.job, "job")
        self.assertEqual(doc.kernel, "kernel")
        self.assertEqual(doc.defconfig, "defconfig")
        self.assertEqual(doc.dtb, "dtb")
        self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        self.assertListEqual([400], errors.keys())

    def test_parse_from_json_no_valid_boot_time(self):
        boot_json = {
            "board": "board",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "dtb": "dtb",
            "boot_time": "foo"
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)

        self.assertIsNotNone(doc)
        self.assertEqual(doc.board, "board")
        self.assertEqual(doc.job, "job")
        self.assertEqual(doc.kernel, "kernel")
        self.assertEqual(doc.defconfig, "defconfig")
        self.assertEqual(doc.git_branch, "branch")
        self.assertEqual(doc.dtb, "dtb")
        self.assertEqual(doc.time, datetime.datetime(1970, 1, 1, 0, 0))
        self.assertListEqual([400], errors.keys())

    def test_parse_from_json_valid(self):
        boot_json = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "boot_time": 0,
        }
        errors = {}

        doc = bimport._parse_boot_from_json(boot_json, self.db, errors)

        self.assertEqual(doc.board, "board")
        self.assertEqual(doc.job, "job")
        self.assertEqual(doc.kernel, "kernel")
        self.assertEqual(doc.defconfig, "defconfig")
        self.assertEqual(doc.dtb, "dtb")
        self.assertDictEqual({}, errors)

    def test_parse_from_json_with_mach_alias(self):
        boot_json = {
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "board": "board",
            "dtb": "dtb",
            "lab_name": "lab_name",
            "git_branch": "branch",
            "mach": "mach",
            "mach_alias": "mach-alias"
        }

        doc = bimport._parse_boot_from_json(boot_json, self.db, {})

        self.assertEqual(doc.mach, "mach-alias")
