#!/bin/sh

# Copyright (C) 2019 Collabora Limited
# Author: Lakshmipathi.G <lakshmipathi.ganapathi@collabora.com>
#
# This script is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

set -e

# Device names and file system type
test_device="${1}"
scratch_device="${2}"

if [ -z "$test_device" ] || [ -z "$scratch_device" ]; then 
    echo "Please check usage."
    echo "Usage: xfstests-config.sh <TEST_DEV> <SCRATCH_DEVICE>"
    exit 1
fi

# Setup xfstests config
cat > /xfstests/local.config <<'EOF'
export TEST_DEV="$test_device"
export TEST_DIR=/test
export SCRATCH_DEV="$scratch_device"
export SCRATCH_MNT=/scratch
#export SCRATCH_DEV_POOL="/dev/xvdc /dev/xvdd /dev/xvde /dev/xvdf /dev/xvdg"
EOF
