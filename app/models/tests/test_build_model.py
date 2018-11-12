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

import unittest

import models.base as modb
import models.build as mbuild


class TestBuildModel(unittest.TestCase):

    def test_build_document_valid_instance(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")
        self.assertIsInstance(build_doc, modb.BaseDocument)
        self.assertIsInstance(build_doc, mbuild.BuildDocument)

    def test_build_document_collection(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")
        self.assertEqual(build_doc.collection, "build")

    def test_build_document_to_dict(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")

        build_doc.id = "build_id"
        build_doc.job_id = "job_id"
        build_doc.created_on = "now"
        build_doc.metadata = {}
        build_doc.status = "FAIL"
        build_doc.dirname = "defconfig"
        build_doc.boot_resul_description = []
        build_doc.errors = 1
        build_doc.warnings = 1
        build_doc.build_time = 1
        build_doc.arch = "foo"
        build_doc.git_url = "git_url"
        build_doc.git_commit = "git_commit"
        build_doc.git_describe = "git_describe"
        build_doc.git_describe_v = "git_describe_v"
        build_doc.version = "1.0"
        build_doc.modules = "modules-file"
        build_doc.dtb_dir = "dtb-dir"
        build_doc.dtb_dir_data = ["a-file"]
        build_doc.kernel_config = "kernel-config"
        build_doc.system_map = "system-map"
        build_doc.text_offset = "offset"
        build_doc.kernel_image = "kernel-image"
        build_doc.modules_dir = "modules-dir"
        build_doc.build_log = "build.log"
        build_doc.kconfig_fragments = "config-frag"
        build_doc.file_server_resource = "file-resource"
        build_doc.file_server_url = "server-url"
        build_doc.build_type = "foo"
        build_doc.defconfig_full = "defconfig_full"
        build_doc.kernel_image_size = 1024
        build_doc.modules_size = 1024
        build_doc.kernel_config_size = 1024
        build_doc.system_map_size = 1024
        build_doc.build_log_size = 1024
        build_doc.kernel_version = "kernel_version"
        build_doc.compiler = "gcc"
        build_doc.compiler_version = "4.7.8"
        build_doc.compiler_version_ext = "gcc 4.7.8"
        build_doc.compiler_version_full = "gcc 4.7.8 full"
        build_doc.cross_compile = "arm"
        build_doc.vmlinux_file_size = 1024
        build_doc.vmlinux_text_size = 1024
        build_doc.vmlinux_bss_size = 1024
        build_doc.vmlinux_data_size = 1024

        expected = {
            "_id": "build_id",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "job_id": "job_id",
            "created_on": "now",
            "metadata": {},
            "status": "FAIL",
            "defconfig": "defconfig",
            "errors": 1,
            "warnings": 1,
            "build_time": 1,
            "arch": "foo",
            "dirname": "defconfig",
            "git_url": "git_url",
            "git_describe": "git_describe",
            "git_branch": "branch",
            "git_commit": "git_commit",
            "build_platform": [],
            "version": "1.0",
            "dtb_dir": "dtb-dir",
            "dtb_dir_data": ["a-file"],
            "kernel_config": "kernel-config",
            "kernel_image": "kernel-image",
            "system_map": "system-map",
            "text_offset": "offset",
            "modules": "modules-file",
            "modules_dir": "modules-dir",
            "build_log": "build.log",
            "kconfig_fragments": "config-frag",
            "defconfig_full": "defconfig_full",
            "file_server_resource": "file-resource",
            "file_server_url": "server-url",
            "build_type": "foo",
            "kernel_image_size": 1024,
            "modules_size": 1024,
            "kernel_config_size": 1024,
            "system_map_size": 1024,
            "build_log_size": 1024,
            "kernel_version": "kernel_version",
            "git_describe_v": "git_describe_v",
            "compiler": "gcc",
            "compiler_version": "4.7.8",
            "compiler_version_full": "gcc 4.7.8 full",
            "cross_compile": "arm",
            "compiler_version_ext": "gcc 4.7.8",
            "vmlinux_file_size": 1024,
            "vmlinux_text_size": 1024,
            "vmlinux_bss_size": 1024,
            "vmlinux_data_size": 1024,
            "build_environment": "build_environment"
        }

        self.assertDictEqual(expected, build_doc.to_dict())

    def test_deconfig_set_status_wrong_and_right(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")

        self.assertRaises(ValueError, setattr, build_doc, "status", "foo")
        self.assertRaises(ValueError, setattr, build_doc, "status", [])
        self.assertRaises(ValueError, setattr, build_doc, "status", {})
        self.assertRaises(ValueError, setattr, build_doc, "status", ())

        build_doc.status = "FAIL"
        self.assertEqual(build_doc.status, "FAIL")
        build_doc.status = "PASS"
        self.assertEqual(build_doc.status, "PASS")
        build_doc.status = "UNKNOWN"
        self.assertEqual(build_doc.status, "UNKNOWN")
        build_doc.status = "BUILD"
        self.assertEqual(build_doc.status, "BUILD")

    def test_defconfig_set_build_platform_wrong(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")

        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", ())
        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", {})
        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", "")

    def test_defconfig_set_build_platform(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")
        build_doc.build_platform = ["a", "b"]

        self.assertListEqual(build_doc.build_platform, ["a", "b"])

    def test_defconfig_set_metadata_wrong(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "branch", "build_environment")

        self.assertRaises(TypeError, setattr, build_doc, "metadata", ())
        self.assertRaises(TypeError, setattr, build_doc, "metadata", [])
        self.assertRaises(TypeError, setattr, build_doc, "metadata", "")

    def test_defconfig_from_json_is_none(self):
        self.assertIsNone(mbuild.BuildDocument.from_json({}))
        self.assertIsNone(mbuild.BuildDocument.from_json(""))
        self.assertIsNone(mbuild.BuildDocument.from_json([]))
        self.assertIsNone(mbuild.BuildDocument.from_json(()))

    def test_build_from_json_wrong(self):
        json_obj = {
            "_id": "build-id"
        }

        self.assertIsNone(mbuild.BuildDocument.from_json(json_obj))

        json_obj = {
            "_id": "build-id",
            "job": "job"
        }

        self.assertIsNone(mbuild.BuildDocument.from_json(json_obj))

        json_obj = {
            "_id": "build-id",
            "job": "job",
            "kernel": "kernel"
        }

        self.assertIsNone(mbuild.BuildDocument.from_json(json_obj))

    def test_defconfog_from_json(self):
        json_obj = {
            "name": "job-kernel-defconfig_full",
            "_id": "build_id",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "job_id": "job_id",
            "created_on": "now",
            "metadata": {
                "foo": "bar"
            },
            "status": "FAIL",
            "defconfig": "defconfig",
            "errors": 1,
            "warnings": 1,
            "build_time": 1,
            "arch": "foo",
            "dirname": "defconfig",
            "git_url": "git_url",
            "git_describe": "git_describe",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "build_platform": [],
            "version": "1.1",
            "dtb_dir": "dtb-dir",
            "dtb_dir_data": ["a-file"],
            "kernel_config": "kernel-config",
            "kernel_image": "kernel-image",
            "system_map": "system-map",
            "text_offset": "offset",
            "modules": "modules-file",
            "modules_dir": "modules-dir",
            "build_log": "build.log",
            "kconfig_fragments": "config-frag",
            "defconfig_full": "defconfig_full",
            "file_server_resource": "file-resource",
            "file_server_url": "server-url",
            "build_type": "kernel",
            "compiler": "gcc",
            "compiler_version": "4.7.8",
            "compiler_version_full": "gcc 4.7.8 full",
            "cross_compile": "arm",
            "compiler_version_ext": "gcc 4.7.8",
            "vmlinux_file": "vmlinux",
            "vmlinux_file_size": 1024,
            "vmlinux_text_size": 1024,
            "vmlinux_bss_size": 1024,
            "vmlinux_data_size": 1024,
            "build_environment": "build_environment"
        }
        build_doc = mbuild.BuildDocument.from_json(json_obj)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.id, "build_id")
        self.assertEqual(build_doc.git_branch, "git_branch")
        self.assertEqual(build_doc.defconfig_full, "defconfig_full")
        self.assertEqual(build_doc.version, "1.1")
        self.assertEqual(build_doc.errors, 1)
        self.assertEqual(build_doc.warnings, 1)
        self.assertEqual(build_doc.build_time, 1)
        self.assertEqual(build_doc.build_type, "kernel")
        self.assertIsNone(build_doc.kernel_image_size)
        self.assertIsNone(build_doc.modules_size)
        self.assertIsNone(build_doc.build_log_size)
        self.assertIsNone(build_doc.system_map_size)
        self.assertIsNone(build_doc.kernel_config_size)
        self.assertListEqual(build_doc.build_platform, [])
        self.assertDictEqual(build_doc.metadata, {"foo": "bar"})
        self.assertEqual(build_doc.compiler, "gcc")
        self.assertEqual(build_doc.compiler_version, "4.7.8")
        self.assertEqual(build_doc.compiler_version_full, "gcc 4.7.8 full")
        self.assertEqual(build_doc.compiler_version_ext, "gcc 4.7.8")
        self.assertEqual(build_doc.cross_compile, "arm")
        self.assertEqual(build_doc.vmlinux_file, "vmlinux")
        self.assertEqual(build_doc.vmlinux_file_size, 1024)
        self.assertEqual(build_doc.vmlinux_text_size, 1024)
        self.assertEqual(build_doc.vmlinux_data_size, 1024)
        self.assertEqual(build_doc.vmlinux_bss_size, 1024)
