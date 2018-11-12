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
import pymongo.errors
import shutil
import tempfile
import types
import unittest

import models.build as mbuild
import models.job as mjob
import utils.build


class TestBuildUtils(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")

        patcher = mock.patch("utils.database.redisdb.get_db_connection")
        mock_open = patcher.start()
        mock_open.return_value = mock.MagicMock()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_traverse_buld_dir_with_ioerror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)

            build_file = os.path.join(build_dir, "build.json")

            with io.open(build_file, mode="w") as write_f:
                write_f.write(json.dumps(dict(foo="bar"), ensure_ascii=False))

            patcher = mock.patch("io.open")
            mock_open = patcher.start()
            mock_open.side_effect = IOError("IOError")
            self.addCleanup(patcher.stop)

            job_doc = mjob.JobDocument("job", "kernel", "git_branch")

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_buld_dir_with_oserror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)

            build_file = os.path.join(build_dir, "build.json")

            with io.open(build_file, mode="w") as write_f:
                write_f.write(json.dumps(dict(foo="bar"), ensure_ascii=False))

            patcher = mock.patch("io.open")
            mock_open = patcher.start()
            mock_open.side_effect = OSError("OSError")
            self.addCleanup(patcher.stop)

            job_doc = mjob.JobDocument("job", "kernel", "git_branch")

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_buld_dir_with_empty_file(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            io.open(os.path.join(build_dir, "build.json"), mode="w")

            job_doc = mjob.JobDocument("job", "kernel", "git_branch")

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_buld_dir_with_json_error(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(u"a string of text")

            job_doc = mjob.JobDocument("job", "kernel", "branch")
            job_doc.created_on = "job_date"

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_build_dir_with_valid_data(self):
        build_data = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "modules_dir": "foo/bar",
            "build_log": "file.log",
            "vmlinux_file": "vmlinux",
            "vmlinux_bss_size": 1024,
            "vmlinux_data_size": 1024,
            "vmlinux_file_size": 1024,
            "vmlinux_text_size": 1024
        }

        job_doc = mjob.JobDocument("job", "kernel", "branch")
        job_doc.created_on = "job_date"

        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(json.dumps(build_data, ensure_ascii=False))

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual("job", build_doc.job)
        self.assertEqual("kernel", build_doc.kernel)
        self.assertEqual("kernel", build_doc.build_type)
        self.assertEqual(build_doc.vmlinux_text_size, 1024)
        self.assertEqual(build_doc.vmlinux_bss_size, 1024)
        self.assertEqual(build_doc.vmlinux_data_size, 1024)
        self.assertEqual(build_doc.vmlinux_file_size, 1024)

    @mock.patch("utils.build.get_artifacts_size")
    def test_traverse_build_dir_data_sizes(self, get_size):
        get_size.return_value = [
            ("system_map_size", 1024),
            ("modules_size", 1025),
            ("build_log_size", 1026),
            ("kernel_config_size", 1027),
            ("kernel_image_size", 1028),
            ("vmlinux_file_size", 1029)
        ]

        build_data = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "modules": "modules.tar",
            "modules_dir": "foo/bar",
            "build_log": "file.log",
            "vmlinux_file": "vmlinux",
            "system_map": "System.map"
        }

        job_doc = mjob.JobDocument("job", "kernel", "git_branch")
        job_doc.created_on = "job_date"

        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(json.dumps(build_data, ensure_ascii=False))

            build_doc = utils.build._traverse_build_dir(
                build_dir, job_doc, errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.system_map_size, 1024)
        self.assertEqual(build_doc.modules_size, 1025)
        self.assertEqual(build_doc.build_log_size, 1026)
        self.assertEqual(build_doc.kernel_config_size, 1027)
        self.assertEqual(build_doc.kernel_image_size, 1028)
        self.assertEqual(build_doc.vmlinux_file_size, 1029)

    def test_parse_build_data_no_version(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.version, "1.1")

    def test_parse_build_data_version(self):
        build_data = {
            "defconfig": "defconfig",
            "version": "foo"
        }
        errors = {}

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.version, "foo")

    def test_parse_build_data_errors_warnings(self):
        build_data = {
            "defconfig": "defconfig",
            "build_errors": 3,
            "build_warnings": 1
        }
        errors = {}

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.errors, 3)
        self.assertEqual(build_doc.warnings, 1)

    def test_parse_build_data_no_job_no_kernel(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.job, "job")
        self.assertEqual(build_doc.kernel, "kernel")

    def test_parse_build_data_no_defconfig_full(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.defconfig_full, "defconfig")

    def test_parse_build_data_diff_fragments(self):
        build_data = {
            "arch": "arm",
            "defconfig": "defoo_confbar",
            "job": "job",
            "kernel": "kernel",
            "kconfig_fragments": "frag-CONFIG_TEST=y.config"
        }

        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", "arm-build_dir")

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(
            build_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(build_doc.defconfig, "defoo_confbar")

    def test_parse_build_metadata(self):
        build_data = {
            "arch": "arm",
            "build_log": "file.log",
            "compiler_version": "gcc version 4.7.3",
            "cross_compile": "arm",
            "defconfig": "defoo_confbar",
            "dtb_dir": "dtbs",
            "git_branch": "test/branch",
            "git_commit": "1234567890",
            "git_describe": "vfoo.bar",
            "git_describe_v": "vfoo.bar.2",
            "git_url": "git://git.example.org",
            "kconfig_fragments": "fragment",
            "kernel_config": "kernel.config",
            "kernel_image": "zImage",
            "kernel_image_size": 2048,
            "modules": "modules.tar",
            "modules_dir": "foo/bar",
            "modules_size": 1024
        }
        build_doc, _ = utils.build.parse_build_data(
            build_data, "job", "kernel", "arm-build_dir")

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertIsInstance(build_doc.metadata, types.DictionaryType)
        self.assertIsInstance(build_doc.dtb_dir_data, types.ListType)
        self.assertDictEqual({}, build_doc.metadata)
        self.assertEqual("gcc", build_doc.compiler)
        self.assertEqual("4.7.3", build_doc.compiler_version)
        self.assertEqual("gcc version 4.7.3", build_doc.compiler_version_full)
        self.assertEqual("arm", build_doc.cross_compile)
        self.assertEqual(build_doc.kconfig_fragments, "fragment")
        self.assertEqual(build_doc.arch, "arm")
        self.assertEqual(build_doc.git_commit, "1234567890")
        self.assertEqual(build_doc.git_branch, "test/branch")
        self.assertEqual(build_doc.git_url, "git://git.example.org")
        self.assertEqual(build_doc.defconfig_full, "defoo_confbar")
        self.assertEqual(build_doc.defconfig, "defoo_confbar")
        self.assertEqual(build_doc.build_log, "file.log")
        self.assertEqual(build_doc.modules_dir, "foo/bar")
        self.assertEqual(build_doc.dtb_dir, "dtbs")
        self.assertEqual(build_doc.kernel_config, "kernel.config")
        self.assertEqual(build_doc.kernel_image, "zImage")
        self.assertEqual(build_doc.build_type, "kernel")
        self.assertEqual(build_doc.modules_size, 1024)
        self.assertEqual(build_doc.kernel_image_size, 2048)
        self.assertEqual(build_doc.git_describe_v, "vfoo.bar.2")

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

    def test_update_job_doc(self):
        job_doc = mjob.JobDocument("job", "kernel", "branch")
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")
        build_doc.git_branch = "branch"
        build_doc.git_commit = "1234567890"
        build_doc.git_describe = "kernel.version"
        build_doc.git_url = "git://url.git"

        utils.build._update_job_doc(
            job_doc, "job_id", "PASS", build_doc, self.db)

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.id)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("job_id", job_doc.id)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_update_job_doc_no_defconfig(self):
        job_doc = mjob.JobDocument("job", "kernel", "branch")

        utils.build._update_job_doc(
            job_doc, None, "PASS", None, self.db)

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNone(job_doc.id)
        self.assertIsNone(job_doc.git_commit)
        self.assertIsNone(job_doc.git_describe)
        self.assertIsNone(job_doc.git_url)

    def test_import_single_build_wrong_name(self):
        json_obj = {
            "job": ".ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        build_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(build_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("os.path.isdir")
    def test_import_single_build_no_build_dir(self, mock_dir):
        mock_dir.return_value = False
        json_obj = {
            "job": ".ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        build_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(build_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_single_build_with_connection_error(self, mock_conn):
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch",
            "git_branch": "branch",
            "build_environment": "build_environment"
        }
        build_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(build_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    @mock.patch("utils.db.save")
    @mock.patch("utils.build._update_job_doc")
    @mock.patch("utils.build._traverse_build_dir")
    @mock.patch("utils.db.find_one2")
    @mock.patch("os.path.isdir")
    def test_import_single_build(
            self, mock_dir, mock_find, mock_tr, mock_up, mock_save, mock_db):
        mock_db = self.db
        mock_dir.return_value = True

        job_doc = {
            "job": "ajob",
            "kernel": "kernel",
            "_id": "job_id",
            "git_branch": "branch"
        }
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")
        build_doc.git_branch = "branch"

        mock_tr.return_value = build_doc
        mock_find.return_value = job_doc
        mock_up.return_value = 201
        mock_save.return_value = (201, "build_id")

        json_obj = {
            "job": "ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "git_branch": "branch",
            "arch": "arch",
            "build_environment": "build_environment"
        }
        build_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertDictEqual({}, errors)
        self.assertIsNotNone(build_id)
        self.assertIsNotNone(job_id)
        self.assertEqual("build_id", build_id)
        self.assertEqual("job_id", job_id)

    def test_extract_kernel_version_no_values(self):
        extracted = utils.build._extract_kernel_version(None, None)
        self.assertIsNone(extracted)

    def test_extract_kernel_version(self):
        extracted = utils.build._extract_kernel_version(
            "v4.1.4-40-g123456", None)
        self.assertEqual("4.1.4", extracted)

    def test_extract_kernel_version_no_v(self):
        extracted = utils.build._extract_kernel_version(
            "4.1.4-40-g123456", None)
        self.assertEqual("4.1.4", extracted)

    def test_extract_kernel_version_no_patches(self):
        extracted = utils.build._extract_kernel_version(
            "v4.1.4", None)
        self.assertEqual("4.1.4", extracted)

    def test_extract_kernel_version_no_git_describe_v(self):
        extracted = utils.build._extract_kernel_version(
            None, "4.4.4")
        self.assertEqual("4.4.4", extracted)

    def test_extract_kernel_version_rc_kernel_no_number(self):
        extracted = utils.build._extract_kernel_version(
            "4.4.4-rc-1234-g12345", None)
        self.assertEqual("4.4.4-rc", extracted)

    def test_extract_kernel_version_rc_kernel_with_number(self):
        extracted = utils.build._extract_kernel_version(
            "4.1-rc12-1234-g12345", None)
        self.assertEqual("4.1-rc12", extracted)

    def test_extract_compiler_data_empty_string(self):
        compiler_version_full = ""
        extracted = utils.build._extract_compiler_data(compiler_version_full)

        self.assertTupleEqual(extracted, (None, None, None, None))

    def test_extract_compiler_data_none(self):
        compiler_version_full = None
        extracted = utils.build._extract_compiler_data(compiler_version_full)

        self.assertTupleEqual(extracted, (None, None, None, None))

    def test_extract_compiler_data_no_compiler_data(self):
        compiler_version_full = "foo"
        extracted = utils.build._extract_compiler_data(compiler_version_full)

        self.assertTupleEqual(extracted, (None, None, None, "foo"))

    def test_extract_compiler_data_gcc_data(self):
        compiler_version_full =\
            "gcc version 4.7.3 (Ubuntu/Linaro 4.7.3-12ubuntu1)"
        extracted = utils.build._extract_compiler_data(compiler_version_full)

        self.assertTupleEqual(
            extracted, ("gcc", "4.7.3", "gcc 4.7.3", compiler_version_full))

    def test_extract_compiler_data_llvm_data(self):
        compiler_version_full = "Apple LLVM version 7.0.2 (clang-700.1.81)"
        extracted = utils.build._extract_compiler_data(compiler_version_full)

        self.assertTupleEqual(
            extracted,
            ("Apple LLVM", "7.0.2", "Apple LLVM 7.0.2", compiler_version_full))

    def test_extract_compiler_data_clang_data(self):
        compiler_version_full = (
            "Debian clang version 3.5.0-10 (tags/RELEASE_350/final) "
            "(based on LLVM 3.5.0)")
        extracted = utils.build._extract_compiler_data(compiler_version_full)
        expected = ("Debian clang",
                    "3.5.0-10", "Debian clang 3.5.0-10", compiler_version_full)

        self.assertTupleEqual(extracted, expected)
