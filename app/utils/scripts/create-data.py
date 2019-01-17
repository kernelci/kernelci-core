#! /usr/bin/python
#
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

import sys
import random
import string

ARCH_LIST = ["arm", "arm64", "mips", "x86"]

DEFCONFIG_LIST = [
    "multi_v7_defconfig",
    "allnoconfig",
    "allmodconfig",
    "tinyconfig",
    "defconfig"
]

DEFCONFIG_FULL_LIST = {
    "defconfig": [
        "defconfig",
        "defconfig+CONFIG_KASAN=y",
        "defconfig+CONFIG_OF_UNITTEST=y",
        "defconfig+CONFIG_VIRTUALIZATION=y",
    ],
    "multi_v7_defconfig": [
        "multi_v7_defconfig",
        "multi_v7_defconfig+CONFIG_CPU_FREQ_GOV_USERSPACE=y",
        "multi_v7_defconfig+CONFIG_EARLY_PRINTK=y",
        "multi_v7_defconfig+CONFIG_PROVE_LOCKING=y,",
        "multi_v7_defconfig+tiny",
    ]
}

COMPILER_VERSION_LIST = {
    "mips": [
        "gcc version 5.3.0 (Sourcery CodeBench Lite 2016.05-8)",
    ],
    "arm64": [
        "gcc version 5.1.1 20150608 (Linaro GCC Snapshot 5.1-2015.06-1)",
        "gcc version 5.2.1 20151005 (Linaro GCC 5.2-2015.11-2)",
        "gcc version 5.3.1 20160113 (Linaro GCC 5.3-2016.02)",
        "gcc version 5.3.1 20160412 (Linaro GCC 5.3-2016.05)",
    ],
    "arm": [
        "gcc version 4.7.4 (Ubuntu/Linaro 4.7.4-2ubuntu1)",
        "gcc version 5.1.1 20150608 (Linaro GCC Snapshot 5.1-2015.06-1)",
        "gcc version 5.3.1 20160113 (Linaro GCC 5.3-2016.02)",
        "gcc version 5.3.1 20160412 (Linaro GCC 5.3-2016.05)"
    ],
    "x86": [
        "gcc version 4.8.5 (Ubuntu 4.8.5-2ubuntu1~14.04.1)",
        "gcc version 4.9.2 (Ubuntu 4.9.2-10ubuntu13)",
        "gcc version 4.9.3 20150113 (prerelease) (Linaro GCC 4.9-2015.01)",
        "gcc version 4.9.3 20150113 (prerelease) (Linaro GCC 4.9-2015.01-1)",
    ]
}

CROSS_COMPILE_LIST = {
    "arm": ["arm-linux-gnueabihf-", "arm-linux-gnueabi-"],
    "arm64": ["aarch64-linux-gnu-"]
}

KERNEL_IMAGE_LIST = [
    "zImage",
    "bzImage",
    "xipImage",
    "Image"
]

GIT_BRANCH_LIST = [
    "local/master",
    "local/dev",
    "local/for-test"
]

BUILD_RESULT = ["PASS", "FAIL"]

GIT_URL_LIST = [
    "https://git.linaro.org/test/example/kernel.git",
    "https://git.kernel.org/pub/scm/linux/kernel/git/example/kernel.git",
    "https://android.googlesource.com/kernel/example"
]

MODULES_LIST = [
    "modules.tar.xz",
    None
]


def create_boot(build, config=None):
    pass


def create_build(job, config=None):

    defconfig = random.choice(DEFCONFIG_LIST)
    if (defconfig in DEFCONFIG_FULL_LIST.keys()):
        defconfig_full = random.choice(DEFCONFIG_FULL_LIST[defconfig])
    else:
        defconfig_full = defconfig

    arch = random.randchoice(ARCH_LIST)
    compiler_version = random.choice(COMPILER_VERSION_LIST[arch])
    if arch in CROSS_COMPILE_LIST.keys():
        cross_compile = random.choice(CROSS_COMPILE_LIST[arch])
    else:
        cross_compile = None

    git_commit = "".join(random.choice(
        string.ascii_lowercase + string.digits) for i in range(40))

    modules = random.choice(MODULES_LIST)
    if modules:
        modules_size = random.randint(1024, 1024 ** 6)
    else:
        modules_size = 0

    build = dict(
        job=job["job"],
        kernel=job["kernel"],
        arch=arch,
        defconfig=defconfig,
        defconfig_full=defconfig_full,
        status=random.choice(BUILD_RESULT),
        build_errors=random.randint(0, 10),
        build_warnings=random.randint(0, 15),
        compile_version=compiler_version,
        cross_compile=cross_compile,
        modules=modules,
        modules_size=modules_size,
        kernel_image=random.choice(KERNEL_IMAGE_LIST),
        kernel_image_size=random.randint(1024, 1024 ** 6),
        git_branch=random.choice(GIT_BRANCH_LIST),
        git_describe=job["kernel"],
        build_time=random.randint(100, 1204 ** 2),
        git_url=random.choice(GIT_URL_LIST),
        git_commit=git_commit
    )

    return build


def create_job(name, config=None):
    if not name:
        name = "test-" + "".join(
            random.choice(string.ascii_lowercase) for i in range(4))

    kernel = "v{:d}.{:d}.{:d}-{:d}-g{:s}".format(
        random.randint(3, 5),
        random.randint(1, 9),
        random.randint(1, 5),
        random.randint(1, 200),
        "".join(random.choice(
            string.ascii_lowercase + string.digits) for i in range(12))
    )

    job = dict(
        job=name,
        kernel=kernel,
        status="PASS"
    )

    return job


def main():
    name = "test-job"
    for i in range(5):
        job = create_job(name)

        for i in range(5):
            build = create_build(job)

    return 0


if __name__ == '__main__':
    sys.exit(main())
