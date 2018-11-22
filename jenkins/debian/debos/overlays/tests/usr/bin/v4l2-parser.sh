#!/bin/sh

# Copyright (C) 2018 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
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

IFS=''

driver_name=$( \
    basename $(readlink -f /sys/class/video4linux/video2/device/driver)) \
    && echo "[kernelci-meta-data] v4l2 driver: $driver_name" \
    || echo "Failed to get v4l2 driver name"

device_name=$( \
    cat /sys/class/video4linux/video2/name) \
    && echo "[kernelci-meta-data] v4l2 device: $device_name" \
    || echo "Failed to get v4l2 device name"

# Test set name
test_set=""

# io index for streaming tests
test_io=""

v4l2-compliance -s | sed s/'\r'/'\n'/g | while read line; do
    # Skip noisy video capture progress messages
    echo "$line" | grep -q 'Video Capture' && continue

    # Keep regular output in the log
    echo "$line"

    # Look for any io number
    echo "$line" | grep -qe '^Test input\|output [0-9]*\:$' && {
        test_io=$( \
            echo $line | \
                sed s/'\(Test [a-z]\+ [0-9]\+\)\:'/'\1'/ | \
                sed s/" "/-/g | \
                sed s/"[\(\)]"//g)
        continue
    }

    # Look for a test set
    echo "$line" | \
        grep -e '^[A-Z].*\:$' | \
        grep -v 'Compliance test' | \
        grep -qv 'Driver Info' && {

        [ -n "$test_set" ] && lava-test-set stop

        test_set=$( \
            echo $line | \
                sed s/'\([A-Z].*\)\:$'/'\1'/g | \
                sed s/" "/-/g | \
                sed s/"[\(\)]"//g)

        [ -n "$test_io" ] && test_set="$test_set"_"$test_io"

        lava-test-set start $test_set

        continue
    }

    # Look for a test case
    echo "$line" | \
        grep -qe "test .*: [OK|FAIL]" && {

        id=$( \
            echo $line | \
                sed s/'\ttest \(.*\): \(.*\)'/'\1'/ | \
                sed s/' '/'-'/g | \
                sed s/"[\(\)']"//g)

        res=$( \
            echo $line | \
                sed s/'\(.*\): \([OK|FAIL].*\)'/'\2'/ | \
                sed s/'OK (Not Supported)'/skip/ | \
                sed s/OK/pass/ | \
                sed s/FAIL/fail/)

        lava-test-case "$id" --result "$res"
    }
done

exit 0
