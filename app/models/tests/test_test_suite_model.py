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
import models.test_suite as mtsuite


class TestTestSuiteModel(unittest.TestCase):

    def test_suite_doc_valid_instance(self):
        test_suite = mtsuite.TestSuiteDocument("name", "lab-name")
        self.assertIsInstance(test_suite, mbase.BaseDocument)

    def test_suite_doc_to_dict(self):
        test_suite = mtsuite.TestSuiteDocument("name", "lab-name")

        test_suite.arch = "arm"
        test_suite.board = "board"
        test_suite.board_instance = 1
        test_suite.boot_log = "boot-log"
        test_suite.boot_log_html = "boot-log-html"
        test_suite.boot_result_description = "boot-result-description"
        test_suite.build_id = "build-id"
        test_suite.compiler = "gcc"
        test_suite.compiler_version = "4.7.3"
        test_suite.compiler_version_full = "gcc version 4.7.3"
        test_suite.created_on = "now"
        test_suite.cross_compile = "cross-compile"
        test_suite.defconfig = "defconfig"
        test_suite.defconfig_full = "defconfig-full"
        test_suite.definition_uri = "uri"
        test_suite.device_type = "device-type"
        test_suite.dtb = "dtb"
        test_suite.dtb_addr = "dtb-addr"
        test_suite.endian = "big-endian"
        test_suite.file_server_resource = "file-resource"
        test_suite.file_server_url = "file-url"
        test_suite.git_branch = "git-branch"
        test_suite.git_commit = "git-commit"
        test_suite.git_describe = "git-describe"
        test_suite.git_url = "git-url"
        test_suite.id = "id"
        test_suite.image_type = "image_type"
        test_suite.initrd_addr = "initrd-addr"
        test_suite.job = "job"
        test_suite.job_id = "job_id"
        test_suite.kernel = "kernel"
        test_suite.kernel_image = "kernel-image"
        test_suite.kernel_image_size = "kernel-image-size"
        test_suite.load_addr = "load-addr"
        test_suite.mach = "mach"
        test_suite.metadata = {"foo": "bar"}
        test_suite.qemu = "qemu"
        test_suite.qemu_command = "qemu-command"
        test_suite.retries = 2
        test_suite.test_case = ["foo"]
        test_suite.test_set = ["bar"]
        test_suite.time = 10
        test_suite.vcs_commit = "1234"
        test_suite.version = "1.1"
        test_suite.warnings = 123

        expected = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "boot_log": "boot-log",
            "boot_log_html": "boot-log-html",
            "boot_result_description": "boot-result-description",
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
            "initrd_addr": "initrd-addr",
            "job": "job",
            "job_id": "job_id",
            "kernel": "kernel",
            "kernel_image": "kernel-image",
            "kernel_image_size": "kernel-image-size",
            "lab_name": "lab-name",
            "load_addr": "load-addr",
            "mach": "mach",
            "metadata": {"foo": "bar"},
            "name": "name",
            "qemu": "qemu",
            "qemu_command": "qemu-command",
            "retries": 2,
            "test_case": ["foo"],
            "test_set": ["bar"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.1",
            "warnings": 123,
        }

        self.assertDictEqual(expected, test_suite.to_dict())

    def test_suite_doc_from_json_missing_key(self):
        test_suite = {
            "_id": "id"
        }

        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(test_suite))

    def test_suite_doc_from_json_wrong_type(self):
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json([]))
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(()))
        self.assertIsNone(mtsuite.TestSuiteDocument.from_json(""))

    def test_suite_doc_from_json(self):
        suite_json = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": 1,
            "boot_log": None,
            "boot_log_html": None,
            "boot_result_description": None,
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
            "image_type": "image_type",
            "initrd_addr": "initrd_addr",
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
            "qemu": None,
            "qemu_command": None,
            "retries": 0,
            "test_case": ["foo"],
            "test_set": ["bar"],
            "time": 10,
            "vcs_commit": "1234",
            "version": "1.0",
            "warnings": 123,
        }

        test_suite = mtsuite.TestSuiteDocument.from_json(suite_json)

        self.assertIsInstance(test_suite, mtsuite.TestSuiteDocument)
        self.assertDictEqual(suite_json, test_suite.to_dict())
