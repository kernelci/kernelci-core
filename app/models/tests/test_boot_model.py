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
import models.boot as mboot


class TestBootModel(unittest.TestCase):

    def test_boot_document_valid_instance(self):
        boot_doc = mboot.BootDocument(
            "board", "job", "kernel", "defconfig", "lab"
        )
        self.assertIsInstance(boot_doc, mbase.BaseDocument)

    def test_boot_document_to_dict(self):
        self.maxDiff = None
        boot_doc = mboot.BootDocument(
            "board", "job", "kernel", "defconfig", "lab", arch="arm"
        )
        boot_doc.id = "id"
        boot_doc.job_id = "job-id"
        boot_doc.created_on = "now"
        boot_doc.defconfig_id = "defconfig_id"
        boot_doc.retries = 10
        boot_doc.version = "1.0"
        boot_doc.dtb_append = False
        boot_doc.boot_log = "boot-log"
        boot_doc.boot_log_html = "boot-log-html"
        boot_doc.warnings = 2
        boot_doc.git_branch = "git-branch"
        boot_doc.git_commit = "git-commit"
        boot_doc.git_describe = "git-describe"
        boot_doc.git_url = "git-url"
        boot_doc.fastboot_cmd = "fastboot"
        boot_doc.defconfig_full = "defconfig"
        boot_doc.file_server_url = "file-server"
        boot_doc.file_server_resource = "file-resource"
        boot_doc.initrd = "initrd"
        boot_doc.board_instance = "instance"

        expected = {
            "_id": "id",
            "board": "board",
            "boot_log": "boot-log",
            "boot_log_html": "boot-log-html",
            "boot_result_description": None,
            "created_on": "now",
            "defconfig": "defconfig",
            "defconfig_id": "defconfig_id",
            "dtb": None,
            "dtb_addr": None,
            "dtb_append": False,
            "endian": None,
            "fastboot": False,
            "initrd_addr": None,
            "job": "job",
            "job_id": "job-id",
            "kernel": "kernel",
            "kernel_image": None,
            "lab_name": "lab",
            "load_addr": None,
            "metadata": {},
            "name": "board-job-kernel-defconfig-arm",
            "retries": 10,
            "status": None,
            "time": 0,
            "version": "1.0",
            "warnings": 2,
            "git_commit": "git-commit",
            "git_branch": "git-branch",
            "git_describe": "git-describe",
            "git_url": "git-url",
            "arch": "arm",
            "fastboot_cmd": "fastboot",
            "defconfig_full": "defconfig",
            "file_server_url": "file-server",
            "file_server_resource": "file-resource",
            "initrd": "initrd",
            "board_instance": "instance"
        }

        self.assertDictEqual(expected, boot_doc.to_dict())

    def test_boot_doc_from_json_missing_key(self):
        boot_json = {
            "_id": "id",
            "name": "boot-name",
            "status": "PASS",
            "warnings": 0
        }

        self.assertIsNone(mboot.BootDocument.from_json(boot_json))

    def test_boot_doc_from_json_wrong_type(self):
        self.assertIsNone(mboot.BootDocument.from_json([]))
        self.assertIsNone(mboot.BootDocument.from_json(()))
        self.assertIsNone(mboot.BootDocument.from_json(""))

    def test_boot_doc_from_json(self):
        self.maxDiff = None
        boot_json = {
            "_id": "id",
            "arch": "arm",
            "board": "board",
            "board_instance": "instance",
            "boot_log": "boot-log",
            "boot_log_html": "boot-log-html",
            "boot_result_description": "desc",
            "created_on": "now",
            "defconfig": "defconfig",
            "defconfig_full": "defconfig_full",
            "defconfig_id": "defconfig_id",
            "dtb": "dtb_val",
            "dtb_addr": "1234",
            "dtb_append": False,
            "endian": "little",
            "fastboot": False,
            "fastboot_cmd": "fastboot",
            "file_server_resource": "file-resource",
            "file_server_url": "file-server",
            "git_branch": "git-branch",
            "git_commit": "git-commit",
            "git_describe": "git-describe",
            "git_url": "git-url",
            "initrd": "initrd",
            "initrd_addr": "1234",
            "job": "job",
            "job_id": "job-id",
            "kernel": "kernel",
            "kernel_image": "kernel_image",
            "lab_name": "lab",
            "load_addr": "12345",
            "metadata": {"foo": "bar"},
            "name": "board-job-kernel-defconfig_full-arm",
            "retries": 10,
            "status": "PASS",
            "time": 0,
            "version": "1.0",
            "warnings": 2
        }

        boot_doc = mboot.BootDocument.from_json(boot_json)

        self.assertIsInstance(boot_doc, mboot.BootDocument)
        self.assertDictEqual(boot_json, boot_doc.to_dict())
