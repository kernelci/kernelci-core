# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2025 Collabora Limited
# Author: Denys Fedoryshchenko <denys.f@collabora.com>

# pylint: disable=C0301

""" Test the APIHelper class """

from kernelci.api.helper import APIHelper
import kernelci.api


def test_apihelper():
    """
    Test the APIHelper class
    (i know i should not be testing private methods, but this is it for now)
    """
    node = {
        "id": "6823c3bafef071f536b6ec3c",
        "kind": "checkout",
        "name": "checkout",
        "path": ["checkout"],
        "group": None,
        "parent": None,
        "state": "done",
        "result": "pass",
        "artifacts": {
            "tarball": "https://files.kernelci.org/linux-mainline-master-v6.15-rc6-52-g9f35e33144ae5.tar.gz"  # noqa: E501
        },
        "data": {
            "kernel_revision": {
                "tree": "mainline",
                "url": "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",
                "branch": "master",
                "commit": "9f35e33144ae5377d6a8de86dd3bd4d995c6ac65",
                "describe": "v6.15-rc6-52-g9f35e33144ae5",
                "version": {
                    "version": 6,
                    "patchlevel": 15,
                    "extra": "-rc6-52-g9f35e33144ae5",
                },
                "commit_tags": [],
                "commit_message": (
                    "x86/its: Fix build errors when CONFIG_MODULES=n\n\n"
                    "Fix several build errors when CONFIG_MODULES=n, including the following:\n\n"
                    "../arch/x86/kernel/alternative.c:195:25: error: incomplete definition of type 'struct module'\n"  # noqa: E501
                    "  195 |         for (int i = 0; i < mod->its_num_pages; i++) {\n\n"
                    'Fixes: 872df34d7c51 ("x86/its: Use dynamic thunks for indirect branches")\n'
                    "Cc: stable@vger.kernel.org\n"
                    "Signed-off-by: Eric Biggers \n"
                    "Acked-by: Dave Hansen \n"
                    "Tested-by: Steven Rostedt (Google) \n"
                    "Reviewed-by: Alexandre Chartre \n"
                    "Signed-off-by: Linus Torvalds "
                ),
                "tip_of_branch": True,
            },
            "architecture_filter": ["x86_64", "arm64", "arm"],
        },
        "debug": {},
        "jobfilter": None,
        "platform_filter": [],
        "created": "2025-05-13T22:12:10.336000",
        "updated": "2025-05-13T22:26:20.157000",
        "timeout": "2025-05-13T23:12:10.327000",
        "holdoff": "2025-05-13T22:25:56.224000",
        "owner": "production",
        "submitter": "service:pipeline",
        "treeid": "c1c7b00a59158432a35f2458f745bfbf142bf513801766850c30f65fdb86d5ab",
        "user_groups": [],
        "processed_by_kcidb_bridge": True,
    }

    configs = kernelci.config.load("tests/configs/api-configs.yaml")
    api_config = configs["api"]["docker-host"]
    testcfg = kernelci.api.get_api(api_config)
    apihelper = APIHelper(testcfg)
    node = apihelper._fsanitize_node_fields(node, "commit_message")  # pylint: disable=protected-access  # noqa: E501
    # Test that the _fsanitize_fsanitize_node_fields method returns a dictionary
    assert isinstance(node, dict)
    # test that commit message doesnt contain single curly braces
    # they should be replaced with double curly braces
    val = node["data"]["kernel_revision"]["commit_message"]
    assert val == (
        "x86/its: Fix build errors when CONFIG_MODULES=n\n\n"
        "Fix several build errors when CONFIG_MODULES=n, including the following:\n\n"
        "../arch/x86/kernel/alternative.c:195:25: error: incomplete definition of type 'struct module'\n"  # noqa: E501
        "  195 |         for (int i = 0; i < mod->its_num_pages; i++) {{\n\n"
        'Fixes: 872df34d7c51 ("x86/its: Use dynamic thunks for indirect branches")\n'
        "Cc: stable@vger.kernel.org\n"
        "Signed-off-by: Eric Biggers \n"
        "Acked-by: Dave Hansen \n"
        "Tested-by: Steven Rostedt (Google) \n"
        "Reviewed-by: Alexandre Chartre \n"
        "Signed-off-by: Linus Torvalds "
    )
