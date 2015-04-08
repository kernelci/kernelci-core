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
import mock
import mongomock
import os
import tempfile
import types
import unittest

from bson import tz_util

import models.defconfig as mdefconfig
import utils
import utils.docimport as docimport


class TestDocImport(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), 'kernel-ci')

    def tearDown(self):
        logging.disable(logging.NOTSET)

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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name, "job", "kernel", "dirname"
            )
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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name, "job", "kernel", "dirname"
            )
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertIsNone(defconf_doc.kconfig_fragments)
        self.assertEqual(defconf_doc.defconfig_full, "defconfig")
        self.assertEqual(defconf_doc.defconfig, "defconfig")

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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name, "job", "kernel", "dirname"
            )
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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name,
                "job",
                "kernel",
                "arm-defoo_confbar+CONFIG_TEST=y"
            )
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(
            defconf_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")

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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name,
                "job",
                "kernel",
                "arm-defoo_confbar"
            )
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(
            defconf_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")

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
            with open(fake_meta.name, 'w') as w_file:
                w_file.write(json.dumps(meta_content))

            defconf_doc = docimport._parse_build_data(
                fake_meta.name,
                "job",
                "kernel",
                "arm-defoo_confbar"
            )
        finally:
            os.unlink(fake_meta.name)

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconf_doc.errors, 3)
        self.assertEqual(defconf_doc.warnings, 1)

    def test_extrapolate_defconfig_full_non_valid(self):
        kconfig_fragments = "foo-CONFIG.bar"
        defconfig = "defconfig"

        self.assertEqual(
            defconfig,
            utils._extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        )

    def test_extrapolate_defconfig_full_valid(self):
        kconfig_fragments = "frag-CONFIG=y.config"
        defconfig = "defconfig"

        expected = "defconfig+CONFIG=y"
        self.assertEqual(
            expected,
            utils._extrapolate_defconfig_full_from_kconfig(
                kconfig_fragments, defconfig)
        )

    def test_extrapolate_defconfig_full_from_dir_non_valid(self):
        dirname = "foo-defconfig+FRAGMENTS"
        self.assertIsNone(
            utils._extrapolate_defconfig_full_from_dirname(dirname))

    def test_extrapolate_defconfig_full_from_dir_valid(self):
        dirname = "arm-defconfig+FRAGMENTS"
        self.assertEqual(
            "defconfig+FRAGMENTS",
            utils._extrapolate_defconfig_full_from_dirname(dirname))

        dirname = "arm64-defconfig+FRAGMENTS"
        self.assertEqual(
            "defconfig+FRAGMENTS",
            utils._extrapolate_defconfig_full_from_dirname(dirname))

        dirname = "x86-defconfig+FRAGMENTS"
        self.assertEqual(
            "defconfig+FRAGMENTS",
            utils._extrapolate_defconfig_full_from_dirname(dirname))
