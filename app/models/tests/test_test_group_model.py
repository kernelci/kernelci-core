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

import models.base as mbase
import models.test_group as mtgroup


class TestTestGroupModel(unittest.TestCase):

    def test_group_doc_valid_instance(self):
        test_group = mtgroup.TestGroupDocument("name", "lab-name")
        self.assertIsInstance(test_group, mbase.BaseDocument)

    def test_group_doc_to_dict(self):
        test_group = mtgroup.TestGroupDocument("name", "lab-name")

        test_group.arch = "arm"
        test_group.board = "board"
        test_group.board_instance = 1
        test_group.boot_log = "boot-log"
        test_group.boot_log_html = "boot-log-html"
        test_group.boot_result_description = "boot-result-description"
        test_group.build_environment = "build-environment"
        test_group.build_id = "build-id"
        test_group.compiler = "gcc"
        test_group.compiler_version = "4.7.3"
        test_group.compiler_version_full = "gcc version 4.7.3"
        test_group.created_on = "now"
        test_group.cross_compile = "cross-compile"
        test_group.defconfig = "defconfig"
        test_group.defconfig_full = "defconfig-full"
        test_group.definition_uri = "uri"
        test_group.device_type = "device-type"
        test_group.dtb = "dtb"
        test_group.dtb_addr = "dtb-addr"
        test_group.endian = "big-endian"
        test_group.file_server_resource = "file-resource"
        test_group.file_server_url = "file-url"
        test_group.git_branch = "git-branch"
        test_group.git_commit = "git-commit"
        test_group.git_describe = "git-describe"
        test_group.git_url = "git-url"
        test_group.id = "id"
        test_group.image_type = "image_type"
        test_group.initrd = "initrd"
        test_group.initrd_addr = "initrd-addr"
        test_group.initrd_info = "initrd-info"
        test_group.job = "job"
        test_group.job_id = "job_id"
        test_group.kernel = "kernel"
        test_group.kernel_image = "kernel-image"
        test_group.kernel_image_size = "kernel-image-size"
        test_group.load_addr = "load-addr"
        test_group.mach = "mach"
        test_group.metadata = {"foo": "bar"}
        test_group.parent_id = "parent-id"
        test_group.qemu = "qemu"
        test_group.qemu_command = "qemu-command"
        test_group.retries = 2
        test_group.sub_groups = [True, False]
        test_group.test_cases = ["foo"]
        test_group.time = 10
        test_group.vcs_commit = "1234"
        test_group.version = "1.1"
        test_group.warnings = 123

        expected = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "boot_log": "boot-log",
            "boot_log_html": "boot-log-html",
            "boot_result_description": "boot-result-description",
            "build_environment": "build-environment",
            "build_id": "build-id",
            "compiler": "gcc",
            "compiler_version": "4.7.3",
            "compiler_version_full": "gcc version 4.7.3",
            "created_on": "now",
            "cross_compile": "cross-compile",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig-full",
            "definition_uri": "uri",
            "device_type": "device-type",
            "dtb": "dtb",
            "dtb_addr": "dtb-addr",
            "endian": "big-endian",
            "file_server_resource": "file-resource",
            "file_server_url": "file-url",
            "git_branch": "git-branch",
            "git_commit": "git-commit",
            "git_describe": "git-describe",
            "git_url": "git-url",
            "image_type": "image_type",
            "initrd": "initrd",
            "initrd_addr": "initrd-addr",
            "initrd_info": "initrd-info",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "kernel_image": "kernel-image",
            "kernel_image_size": "kernel-image-size",
            "lab_name": "lab-name",
            "load_addr": "load-addr",
            "mach": "mach",
            "metadata": {"foo": "bar"},
            "parent_id": "parent-id",
            "name": "name",
            "qemu": "qemu",
            "qemu_command": "qemu-command",
            "retries": 2,
            "sub_groups": [True, False],
            "test_cases": ["foo"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.1",
            "warnings": 123,
        }

        self.assertDictEqual(expected, test_group.to_dict())

    def test_group_doc_from_json_missing_key(self):
        test_group = {
            "_id": "id"
        }

        self.assertIsNone(mtgroup.TestGroupDocument.from_json(test_group))

    def test_group_doc_from_json_wrong_type(self):
        self.assertIsNone(mtgroup.TestGroupDocument.from_json([]))
        self.assertIsNone(mtgroup.TestGroupDocument.from_json(()))
        self.assertIsNone(mtgroup.TestGroupDocument.from_json(""))

    def test_group_doc_from_json(self):
        group_json = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "boot_log": None,
            "boot_log_html": None,
            "boot_result_description": None,
            "build_environment": "build-environment",
            "build_id": "build-id",
            "compiler": None,
            "compiler_version": None,
            "compiler_version_full": None,
            "created_on": "now",
            "cross_compile": None,
            "defconfig": "defconfig",
            "defconfig_full": "defconfig",
            "definition_uri": "uri",
            "device_type": "device-type",
            "dtb": None,
            "dtb_addr": None,
            "endian": None,
            "file_server_resource": None,
            "file_server_url": None,
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "git_describe": "git_describe",
            "git_url": "git_url",
            "initrd": "initrd",
            "image_type": "image_type",
            "initrd_addr": "initrd_addr",
            "initrd_info": None,
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "kernel_image": None,
            "kernel_image_size": None,
            "lab_name": "lab-name",
            "load_addr": "load_addr",
            "mach": "mach",
            "metadata": {"foo": "bar"},
            "name": "name",
            "parent_id": "parent-id",
            "qemu": None,
            "qemu_command": None,
            "retries": 0,
            "sub_groups": [True, False],
            "test_cases": ["foo"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.0",
            "warnings": 123,
        }

        test_group = mtgroup.TestGroupDocument.from_json(group_json)

        self.assertIsInstance(test_group, mtgroup.TestGroupDocument)
        self.assertDictEqual(group_json, test_group.to_dict())
