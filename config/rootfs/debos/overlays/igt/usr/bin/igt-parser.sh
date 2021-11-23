#!/bin/sh

# Copyright (C) 2019 Collabora Limited
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

# List of i-g-t test binaries to run
tests=$*

[ -z "$tests" ] && {
    echo "No tests provided"
    exit 1
}

# For debugging this script outside of LAVA jobs
LC_ALL=C type lava-test-set > /dev/null || alias lava-test-set='echo - '
LC_ALL=C type lava-test-case > /dev/null || alias lava-test-case='echo --- '

# Standard installation path for i-g-t test binaries
export PATH=/usr/libexec/igt-gpu-tools:/usr/libexec/igt-gpu-tools/amdgpu:$PATH

# See lib/igt_core.h
IGT_EXIT_SUCCESS=0
IGT_EXIT_INVALID=79
IGT_EXIT_FAILURE=98
IGT_EXIT_SKIP=77

# Check the test case exit status and report the result
test_case_status()
{
    name="$1"
    stat="$2"

    case $stat in
        $IGT_EXIT_SUCCESS)
            res="pass"
            ;;
        $IGT_EXIT_FAILURE)
            res="fail"
            ;;
        $IGT_EXIT_SKIP)
            res="skip"
            ;;
        $IGT_EXIT_INVALID)
            echo "WARNING: invalid subtest $t/$sub"
            res="skip"
            ;;
        *)
            echo "WARNING: unhandled exit status: $stat"
            res="skip"
            ;;
    esac

    lava-test-case "$name" --result "$res"
}

# Run all the tests and report their results
for cmd in $tests; do
    subtests=$($cmd --list-subtests)

    if [ -n "$subtests" ]; then
        lava-test-set start $cmd
        for sub in $subtests; do
            $cmd --run-subtest $sub
            test_case_status $sub $?
        done
        lava-test-set stop $cmd
    else
        $cmd
        test_case_status $cmd $?
    fi
done

exit 0
