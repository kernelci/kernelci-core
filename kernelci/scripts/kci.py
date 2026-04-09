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

# Import subcommand modules for their Click registration side effects.
from kernelci.cli import (  # pylint: disable=unused-import  # noqa: F401,E402
    api as kci_api,
)
from kernelci.cli import (
    config as kci_config,
)
from kernelci.cli import (
    docker as kci_docker,
)
from kernelci.cli import (
    event as kci_event,
)
from kernelci.cli import (
    job as kci_job,
)
from kernelci.cli import kci  # noqa: E402
from kernelci.cli import (
    node as kci_node,
)
from kernelci.cli import (
    storage as kci_storage,
)
from kernelci.cli import (
    user as kci_user,
)


def main():
    kci()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
