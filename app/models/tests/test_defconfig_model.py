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
import models.defconfig as moddf


class TestDefconfModel(unittest.TestCase):

    def test_defconfig_document_valid_instance(self):
        defconf_doc = moddf.DefconfigDocument('job', 'kernel', 'defconfig')
        self.assertIsInstance(defconf_doc, modb.BaseDocument)
        self.assertIsInstance(defconf_doc, moddf.DefconfigDocument)

    def test_defconfig_document_collection(self):
        defconfig_doc = moddf.DefconfigDocument('job', 'kernel', 'defconfig')
        self.assertEqual(defconfig_doc.collection, 'defconfig')

    def test_defconfig_document_to_dict(self):
        defconf_doc = moddf.DefconfigDocument(
            'job', 'kernel', 'defconfig', 'defconfig_full')
        defconf_doc.id = "defconfig_id"
        defconf_doc.job_id = "job_id"
        defconf_doc.created_on = "now"
        defconf_doc.metadata = {}
        defconf_doc.status = "FAIL"
        defconf_doc.dirname = "defconfig"
        defconf_doc.boot_resul_description = []
        defconf_doc.errors = 1
        defconf_doc.warnings = 1
        defconf_doc.build_time = 1
        defconf_doc.arch = "foo"
        defconf_doc.git_url = "git_url"
        defconf_doc.git_commit = "git_commit"
        defconf_doc.git_branch = "git_branch"
        defconf_doc.git_describe = "git_describe"
        defconf_doc.version = "1.0"
        defconf_doc.modules = "modules-file"
        defconf_doc.dtb_dir = "dtb-dir"
        defconf_doc.kernel_config = "kernel-config"
        defconf_doc.system_map = "system-map"
        defconf_doc.text_offset = "offset"
        defconf_doc.kernel_image = "kernel-image"
        defconf_doc.modules_dir = "modules-dir"
        defconf_doc.build_log = "build.log"
        defconf_doc.kconfig_fragments = "config-frag"
        defconf_doc.file_server_resource = "file-resource"
        defconf_doc.file_server_url = "server-url"

        expected = {
            "name": "job-kernel-defconfig_full",
            "_id": "defconfig_id",
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
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "build_platform": [],
            "version": "1.0",
            "dtb_dir": "dtb-dir",
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
        }

        self.assertDictEqual(expected, defconf_doc.to_dict())

    def test_deconfig_set_status_wrong_and_right(self):
        defconf_doc = moddf.DefconfigDocument("job", "kernel", "defconfig")

        self.assertRaises(ValueError, setattr, defconf_doc, "status", "foo")
        self.assertRaises(ValueError, setattr, defconf_doc, "status", [])
        self.assertRaises(ValueError, setattr, defconf_doc, "status", {})
        self.assertRaises(ValueError, setattr, defconf_doc, "status", ())

        defconf_doc.status = "FAIL"
        self.assertEqual(defconf_doc.status, "FAIL")
        defconf_doc.status = "PASS"
        self.assertEqual(defconf_doc.status, "PASS")
        defconf_doc.status = "UNKNOWN"
        self.assertEqual(defconf_doc.status, "UNKNOWN")
        defconf_doc.status = "BUILD"
        self.assertEqual(defconf_doc.status, "BUILD")

    def test_defconfig_set_build_platform_wrong(self):
        defconf_doc = moddf.DefconfigDocument("job", "kernel", "defconfig")

        self.assertRaises(
            TypeError, setattr, defconf_doc, "build_platform", ())
        self.assertRaises(
            TypeError, setattr, defconf_doc, "build_platform", {})
        self.assertRaises(
            TypeError, setattr, defconf_doc, "build_platform", "")

    def test_defconfig_set_build_platform(self):
        defconf_doc = moddf.DefconfigDocument("job", "kernel", "defconfig")
        defconf_doc.build_platform = ["a", "b"]

        self.assertListEqual(defconf_doc.build_platform, ["a", "b"])

    def test_defconfig_set_metadata_wrong(self):
        defconf_doc = moddf.DefconfigDocument("job", "kernel", "defconfig")

        self.assertRaises(TypeError, setattr, defconf_doc, "metadata", ())
        self.assertRaises(TypeError, setattr, defconf_doc, "metadata", [])
        self.assertRaises(TypeError, setattr, defconf_doc, "metadata", "")

    def test_defconfig_from_json_is_none(self):
        self.assertIsNone(moddf.DefconfigDocument.from_json({}))
        self.assertIsNone(moddf.DefconfigDocument.from_json(""))
        self.assertIsNone(moddf.DefconfigDocument.from_json([]))
        self.assertIsNone(moddf.DefconfigDocument.from_json(()))
