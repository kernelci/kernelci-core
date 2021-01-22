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

# Video driver name
driver_name="${1}"

[ -z "$driver_name" ] && {
    echo "No driver name provided"
    echo "Usage: v4l2-parser.sh <DRIVER_NAME>"
    exit 1
}

IFS=''

# Test set name
test_set=""

# io index for streaming tests
test_io=""

device_path=$(v4l2-get-device -d $driver_name | head -n1)

[ -z "$device_path" ] && {
    echo "No device found for driver $driver_name"
    lava-test-case device-presence --result fail
    exit 1
}

lava-test-case device-presence --result pass
echo "device: $device_path"

v4l2-compliance -s -d $device_path | sed s/'\r'/'\n'/g | while read line; do
    # Skip noisy video capture progress messages
    echo "$line" | grep -q 'Video Capture\|Output' && continue

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
                sed s/'OK (Not Supported)'/pass/ | \
                sed s/OK/pass/ | \
                sed s/FAIL/fail/)

        lava-test-case "$id" --result "$res"
    }
done

exit 0
