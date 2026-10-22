# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2026 Jiakai Xu

"""QEMU container image configuration in generated LAVA jobs."""

import pytest
import yaml

from kernelci.config.job import Job as JobConfig
from kernelci.config.platform import Platform
from kernelci.config.runtime import RuntimeLAVA
from kernelci.runtime import Job
from kernelci.runtime.lava import LAVA


@pytest.mark.parametrize("arch", ["arm64", "x86_64"])
@pytest.mark.parametrize("boot_commands", ["ramdisk", "rootfs"])
@pytest.mark.parametrize(
    "platform_params,job_params,expected_image",
    [
        pytest.param({}, {}, "kernelci/qemu", id="default"),
        pytest.param(
            {"qemu_docker_image": "registry.example.com:5000/qemu:stable"},
            {},
            "registry.example.com:5000/qemu:stable",
            id="platform",
        ),
        pytest.param(
            {},
            {"qemu_docker_image": "registry.example.com/qemu:latest"},
            "registry.example.com/qemu:latest",
            id="job",
        ),
        pytest.param(
            {"qemu_docker_image": "registry.example.com/qemu:platform"},
            {"qemu_docker_image": "registry.example.com/qemu:job"},
            "registry.example.com/qemu:job",
            id="job-overrides-platform",
        ),
        pytest.param(
            {}, {"qemu_docker_image": None}, "kernelci/qemu", id="null"
        ),
        pytest.param(
            {}, {"qemu_docker_image": ""}, "kernelci/qemu", id="empty"
        ),
        pytest.param(
            {},
            {
                "qemu_docker_image": "registry.example.com/qemu@sha256:"
                + "a" * 64
            },
            "registry.example.com/qemu@sha256:" + "a" * 64,
            id="digest",
        ),
    ],
)
def test_qemu_docker_image(
    arch, boot_commands, platform_params, job_params, expected_image, mocker
):
    """Render platform/job overrides through the real LAVA runtime offline."""
    mocker.patch(
        "requests.sessions.Session.request",
        side_effect=AssertionError("Job generation must not contact a service"),
    )
    config = JobConfig(
        name="baseline",
        template="base/lava.jinja2",
        params={
            "boot_commands": boot_commands,
            "test_method": "baseline",
            "ramdiskroot": "https://example.com/rootfs",
            "ramdisk": "https://example.com/rootfs.cpio.gz",
            **job_params,
        },
    )
    job = Job(
        {
            "id": "qemu-test",
            "name": "baseline",
            "data": {"kernel_revision": {"describe": "v6.12"}},
            "artifacts": {
                "kernel": "https://example.com/Image",
                "modules": "https://example.com/modules.tar.xz",
            },
        },
        config,
    )
    job.platform_config = Platform(
        name=f"qemu-{arch}",
        arch=arch,
        boot_method="qemu",
        context={"arch": arch},
        params=platform_params,
    )
    runtime = LAVA(RuntimeLAVA(name="test-lab", lab_type="lava"))

    definition = yaml.safe_load(runtime.generate(job, runtime.get_params(job)))

    assert definition["actions"][1]["boot"]["docker"] == {
        "binary": f"qemu-system-{arch}",
        "image": expected_image,
    }
