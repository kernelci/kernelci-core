#!/usr/bin/env python3
#
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022-2024 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
# Author: Jeny Sadadia <jeny.sadadia@collabora.com>

"""KernelCI Command Line Tool entrypoint"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from kernelci.cli import kci  # noqa: E402
from kernelci.cli import (  # pylint: disable=unused-import  # noqa: E402
    api as kci_api,
    config as kci_config,
    docker as kci_docker,
    event as kci_event,
    job as kci_job,
    node as kci_node,
    storage as kci_storage,
    user as kci_user,
)


def main():
    kci()  # pylint: disable=no-value-for-parameter


if __name__ == '__main__':
    main()
