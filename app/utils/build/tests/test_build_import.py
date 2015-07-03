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

import models.defconfig as mdefconfig
import models.job as mjob
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

    def test_traverse_buld_dir_with_ioerror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            io.open(os.path.join(build_dir, "build.json"), mode="w")

            patcher = mock.patch("io.open")
            mock_open = patcher.start()
            mock_open.side_effect = IOError("IOError")
            self.addCleanup(patcher.stop)

            defconfig_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(defconfig_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_buld_dir_with_jsonerror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(u"a string of text")

            defconfig_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(defconfig_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_build_dir_with_valid_data(self):
        build_data = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "modules_dir": "foo/bar",
            "build_log": "file.log"
        }

        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(json.dumps(build_data, ensure_ascii=False))

            defconfig_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual("job", defconfig_doc.job)
        self.assertEqual("kernel", defconfig_doc.kernel)

    def test_parse_build_data_no_dict(self):
        build_data = []
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsNone(defconfig_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    def test_parse_build_data_missing_key(self):
        build_data = {"arch": "arm"}
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsNone(defconfig_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    def test_parse_build_data_no_version(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconfig_doc.version, "1.0")

    def test_parse_build_data_version(self):
        build_data = {
            "defconfig": "defconfig",
            "version": "foo"
        }
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconfig_doc.version, "foo")

    def test_parse_build_data_errors_warnings(self):
        build_data = {
            "defconfig": "defconfig",
            "build_errors": 3,
            "build_warnings": 1
        }
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconfig_doc.errors, 3)
        self.assertEqual(defconfig_doc.warnings, 1)

    def test_parse_build_data_no_job_no_kernel(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconfig_doc.job, "job")
        self.assertEqual(defconfig_doc.kernel, "kernel")

    def test_parse_build_data_no_defconfig_full(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(defconfig_doc.defconfig_full, "defconfig")

    def test_parse_build_data_diff_fragments(self):
        build_data = {
            "arch": "arm",
            "defconfig": "defoo_confbar",
            "job": "job",
            "kernel": "kernel",
            "kconfig_fragments": "frag-CONFIG_TEST=y.config"
        }

        defconfig_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", {}, "arm-build_dir")

        self.assertIsInstance(defconfig_doc, mdefconfig.DefconfigDocument)
        self.assertEqual(
            defconfig_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(defconfig_doc.defconfig, "defoo_confbar")

    def test_parse_build_metadata(self):
        build_data = {
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
            "kconfig_fragments": "fragment",
            "compiler_version": "gcc",
            "cross_compile": "foo"
        }
        defconf_doc = utils.build._parse_build_data(
            build_data, "job", "kernel", {}, "arm-build_dir")

        self.assertIsInstance(defconf_doc, mdefconfig.DefconfigDocument)
        self.assertIsInstance(defconf_doc.metadata, types.DictionaryType)
        self.assertIsInstance(defconf_doc.dtb_dir_data, types.ListType)
        self.assertNotEqual({}, defconf_doc.metadata)
        self.assertEqual("gcc", defconf_doc.metadata["compiler_version"])
        self.assertEqual("foo", defconf_doc.metadata["cross_compile"])
        self.assertEqual(defconf_doc.kconfig_fragments, "fragment")
        self.assertEqual(defconf_doc.arch, "arm")
        self.assertEqual(defconf_doc.git_commit, "1234567890")
        self.assertEqual(defconf_doc.git_branch, "test/branch")
        self.assertEqual(defconf_doc.git_url, "git://git.example.org")
        self.assertEqual(defconf_doc.defconfig_full, "defoo_confbar")
        self.assertEqual(defconf_doc.defconfig, "defoo_confbar")
        self.assertEqual(defconf_doc.build_log, "file.log")
        self.assertEqual(defconf_doc.modules_dir, "foo/bar")
        self.assertEqual(defconf_doc.dtb_dir, "dtbs")
        self.assertEqual(defconf_doc.kernel_config, "kernel.config")
        self.assertEqual(defconf_doc.kernel_image, "zImage")

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

    @mock.patch("utils.build._traverse_build_dir")
    @mock.patch("os.path.exists")
    def test_traverse_kernel_dir_fake(self, mock_exists, mock_trav):
        mock_exists.return_value = True
        mock_trav.side_effect = [None, None, None, "foo"]
        kernel_dir = tempfile.mkdtemp()

        def scan_func(to_scan):
            yield None
            yield None
            yield None
            yield None

        try:
            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir,
                "job",
                "kernel", "job_id", "job_date", {}, scan_func=scan_func)
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertListEqual(["foo"], docs)
        self.assertEqual("PASS", job_status)
        self.assertDictEqual({}, errors)

    def test_traverse_kernel_dir_building(self):
        kernel_dir = tempfile.mkdtemp()
        try:
            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir, "job", "kernel", "job_id", "job_date", {})
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertEqual("BUILD", job_status)
        self.assertListEqual([], docs)
        self.assertDictEqual({}, errors)

    def test_traverse_kernel_dir(self):
        kernel_dir = tempfile.mkdtemp()
        build_dir = os.path.join(kernel_dir, "arm-fake_defconfig")
        build_data = {
            "arch": "arm",
            "defconfig": "fake_defconfig",
            "kernel": "kernel",
            "job": "job"
        }
        try:
            os.mkdir(build_dir)
            io.open(os.path.join(kernel_dir, ".done"), mode="w")
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as w:
                w.write(json.dumps(build_data, ensure_ascii=False))

            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir, "job", "kernel", "job_id", "job_date", {})
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertEqual("PASS", job_status)
        self.assertDictEqual({}, errors)
        self.assertEqual(1, len(docs))
        self.assertEqual("fake_defconfig", docs[0].defconfig)

    def test_update_job_doc(self):
        job_doc = mjob.JobDocument("job", "kernel")
        defconfig_doc = mdefconfig.DefconfigDocument(
            "job", "kernel", "defconfig")
        defconfig_doc.git_branch = "local/branch"
        defconfig_doc.git_commit = "1234567890"
        defconfig_doc.git_describe = "kernel.version"
        defconfig_doc.git_url = "git://url.git"

        utils.build._update_job_doc(job_doc, "PASS", [defconfig_doc])

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_update_job_doc_no_defconfig(self):
        job_doc = mjob.JobDocument("job", "kernel")

        utils.build._update_job_doc(job_doc, "PASS", [])

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNone(job_doc.git_branch)
        self.assertIsNone(job_doc.git_commit)
        self.assertIsNone(job_doc.git_describe)
        self.assertIsNone(job_doc.git_url)

    def test_update_job_doc_with_job_doc_and_fake(self):
        job_doc = mjob.JobDocument("job", "kernel")
        job_doc_b = mjob.JobDocument("job", "kernel")
        defconfig_doc = mdefconfig.DefconfigDocument(
            "job", "kernel", "defconfig")
        defconfig_doc.git_branch = "local/branch"
        defconfig_doc.git_commit = "1234567890"
        defconfig_doc.git_describe = "kernel.version"
        defconfig_doc.git_url = "git://url.git"

        utils.build._update_job_doc(
            job_doc, "PASS", [job_doc_b, {"foo": "bar"}, defconfig_doc])

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_update_job_doc_with_job_doc_fake_and_wrong(self):
        job_doc = mjob.JobDocument("job", "kernel")
        job_doc_b = mjob.JobDocument("job", "kernel")
        defconfig_doc = mdefconfig.DefconfigDocument(
            "job", "kernel", "defconfig")
        defconfig_doc.git_branch = "local/branch"
        defconfig_doc.git_commit = "1234567890"
        defconfig_doc.git_describe = "kernel.version"
        defconfig_doc.git_url = "git://url.git"

        defconfig_doc_b = mdefconfig.DefconfigDocument(
            "job_b", "kernel_b", "defconfig_b")

        utils.build._update_job_doc(
            job_doc,
            "PASS",
            [job_doc_b, defconfig_doc_b, {"foo": "bar"}, defconfig_doc]
        )

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)
