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

try:
    import simplejson as json
except ImportError:
    import json

import datetime
import io
import logging
import mock
import mongomock
import os
import tempfile
import types
import unittest
import shutil
import pymongo.errors

from bson import tz_util

import models.defconfig as mdefconfig
import utils.build


class TestBuildUtils(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_import_with_dot_name(self):
        json_obj = {
            "job": ".job",
            "kernel": ".kernel"
        }
        job_id, errors = utils.build.import_from_dir(
            json_obj, {}, base_path=utils.BASE_PATH)

        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_with_connection_error(self, mock_conn):
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        job_id, errors = utils.build.import_from_dir(json_obj, {})
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_from_dir_connection_error(self, mock_conn, mock_import):
        mock_import.return_value = (["docs"], "job-id", {400: ["error"]})
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_from_dir(json_obj, {})
        self.assertIsNotNone(errors)
        self.assertListEqual([400, 500], errors.keys())

    @mock.patch("utils.db.save_all")
    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_from_dir_save_error(
            self, mock_conn, mock_import, mock_save):
        mock_conn = self.db
        mock_import.return_value = (["docs"], "job-id", {500: ["error"]})
        mock_save.return_value = (500, None)

        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_from_dir(json_obj, {})
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.save_all")
    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_from_dir_no_save_error(
            self, mock_conn, mock_import, mock_save):
        mock_conn = self.db
        mock_import.return_value = (["docs"], "job-id", {})
        mock_save.return_value = (201, None)

        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_from_dir(json_obj, {})
        self.assertDictEqual({}, errors)

    def test_parse_and_update_build_metadata_errors(self):
        meta_content = {
            "arch": "arm",
            "defconfig": "defoo_confbar",
            "job": "job",
            "kernel": "kernel",
            "build_errors": 3,
            "build_warnings": 1,
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconf_doc.errors, 3)
        self.assertEqual(defconf_doc.warnings, 1)

    def test_parse_and_update_build_metadata_diff_fragments(self):
        meta_content = {
            "arch": "arm",
            "defconfig": "defoo_confbar",
            "job": "job",
            "kernel": "kernel",
            "kconfig_fragments": "frag-CONFIG_TEST=y.config"
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(
            defconf_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")

    def test_parse_and_update_build_metadata_with_fragments(self):
        meta_content = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "dtb_dir": "dtbs",
            "modules_dir": "foo/bar",
            "build_log": "file.log",
            "kconfig_fragments": "frag-CONFIG_TEST=y.config"
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(
            defconf_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")

    def test_parse_and_update_build_metadata(self):
        meta_content = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "dtb_dir": "dtbs",
            "modules_dir": "foo/bar",
            "build_log": "file.log",
            "kconfig_fragments": "fragment"
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertIsInstance(defconf_doc.metadata, types.DictionaryType)
        self.assertEqual(defconf_doc.kconfig_fragments, "fragment")
        self.assertEqual(defconf_doc.arch, "arm")
        self.assertEqual(defconf_doc.git_commit, "1234567890")
        self.assertEqual(defconf_doc.git_branch, "test/branch")
        self.assertEqual(defconf_doc.defconfig_full, "defoo_confbar")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")

    @mock.patch("os.stat")
    def test_parse_build_data_missing_key(self, mock_stat):
        mock_stat.st_mtime.return_value = datetime.datetime.now(tz=tz_util.utc)
        meta_content = {
            "arch": "arm",
            "job": "job",
            "kernel": "kernel"
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsNone(defconf_doc)

    def test_parse_build_data_no_fragments_no_full(self):
        meta_content = {
            "arch": "arm",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig"
        }

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(json.dumps(meta_content, ensure_ascii=False))

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", {})
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertIsNone(defconf_doc.kconfig_fragments)
        self.assertEqual(defconf_doc.defconfig_full, "defconfig")
        self.assertEqual(defconf_doc.defconfig, "defconfig")

    def test_parse_build_data_jsonerror(self):
        meta_content = u"a string of text"
        errors = {}

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)
            with io.open(fake_meta.name, mode="w") as w_file:
                w_file.write(meta_content)

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", errors)
        finally:
            os.unlink(fake_meta.name)

        self.assertIsNone(defconf_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("io.open")
    def test_parse_build_data_ioerror(self, mock_open):
        mock_open.side_effect = IOError("IOError")
        errors = {}

        try:
            fake_meta = tempfile.NamedTemporaryFile(delete=False)

            defconf_doc = utils.build._parse_build_data(
                os.path.basename(fake_meta.name),
                os.path.dirname(fake_meta.name), "job", "kernel", errors)
        finally:
            os.unlink(fake_meta.name)

        self.assertIsNone(defconf_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    def test_parse_dtb_dir_single_file(self):
        temp_dir = tempfile.mkdtemp()
        expected = ["arm-dtb/arm.dtb"]
        try:
            dtb_dir = os.path.join(temp_dir, "dtbs")
            os.mkdir(dtb_dir)
            arm_dtb_dir = os.path.join(dtb_dir, "arm-dtb")
            arm_dtb_file = os.path.join(arm_dtb_dir, "arm.dtb")
            os.mkdir(arm_dtb_dir)
            io.open(arm_dtb_file, mode="w")

            results = utils.build.parse_dtb_dir(temp_dir, "dtbs")
            self.assertListEqual(expected, results)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parse_dtb_dir_complex_case(self):
        temp_dir = tempfile.mkdtemp()
        expected = ["a-dtb.dtb", "arm-dtb/arm.dtb"]
        try:
            dtb_dir = os.path.join(temp_dir, "dtbs")
            os.mkdir(dtb_dir)
            os.mkdir(os.path.join(dtb_dir, ".fake-dtb-dir"))
            arm_dtb_dir = os.path.join(dtb_dir, "arm-dtb")
            arm_dtb_file = os.path.join(arm_dtb_dir, "arm.dtb")
            os.mkdir(arm_dtb_dir)
            io.open(arm_dtb_file, mode="w")
            io.open(os.path.join(arm_dtb_dir, ".fake-file.dtb"), mode="w")
            io.open(os.path.join(dtb_dir, "a-dtb.dtb"), mode="w")

            results = utils.build.parse_dtb_dir(temp_dir, "dtbs")
            self.assertListEqual(expected, results)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
