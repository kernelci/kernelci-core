# SPDX-License-Identifier: LGPL-2.1-or-later

"""Rendering tests for EFI rootfs selection."""

import unittest
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from kernelci.config import resolve_rootfs_params


class EfiTemplateTest(unittest.TestCase):
    def render(self, **overrides):
        """Render EFI actions with representative job parameters."""
        template_dir = Path(__file__).parents[1] / "config" / "runtime"
        template = Environment(
            loader=FileSystemLoader(template_dir)
        ).get_template("boot/efi.jinja2")
        params = {
            "boot_commands": "nfs",
            "brarch": "aarch64",
            "device_dtb": "dtbs/qcom/test.dtb",
            "platform_config": {
                "name": "test-platform",
                "flash_image": "https://example.com/flash.img",
            },
            "node": {
                "artifacts": {
                    "dtb": "https://example.com/test.dtb",
                    "kernel": "https://example.com/Image",
                    "modules": "https://example.com/modules.tar.xz",
                    "kselftest_tar_xz": "https://example.com/kselftest.tar.xz",
                },
                "data": {"kernel_type": "image"},
            },
            "ramdiskroot": "https://example.com/buildroot",
        }
        params.update(overrides)
        return yaml.safe_load(template.render(params))[0]["deploy"]

    def test_configured_initrd(self):
        """EFI honors the configured initrd instead of a fixed image."""
        url = "https://example.com/custom/initrd.cpio.gz"
        deploy = self.render(ramdisk=url)
        self.assertEqual(deploy["images"]["ramdisk"]["url"], url)

    def test_rootfs_reference(self):
        """An initrd resolved from rootfs configuration reaches the job."""
        url = "https://example.com/rootfs/initrd.cpio.gz"
        params = {"rootfs_ref": "custom"}
        resolve_rootfs_params(params, {"custom": {"ramdisk": url}})
        deploy = self.render(**params)
        self.assertEqual(deploy["images"]["ramdisk"]["url"], url)

    def test_ramdisk_boot(self):
        """Ramdisk boot keeps its Buildroot image and kselftest overlay."""
        deploy = self.render(
            boot_commands="ramdisk",
            ramdisk="https://example.com/unused/initrd.cpio.gz",
        )
        ramdisk = deploy["images"]["ramdisk"]
        self.assertEqual(
            ramdisk["url"], "https://example.com/buildroot/rootfs.cpio.gz"
        )
        self.assertIn("kselftest", ramdisk["overlays"])


if __name__ == "__main__":
    unittest.main()
