#!/bin/sh
#
# Copyright (C) 2025 Collabora Limited
# Author: Benjamin Gaignard <benjamin.gaignard@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
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

if [ "$KERNELCI_LAVA" = "y" ]; then
    alias test-result='lava-test-case'
    alias test-exception='lava-test-raise'
else
    alias test-result='echo'
    alias test-exception='echo'
fi

if ! command -v gst-inspect-1.0 >/dev/null; then
	echo "gst-inspect-1.0 not found. Please install it to proceed."
	test-result h26forge-debian --result skip
	exit 0
fi

# Check if v4l2slh264dec element exist
if command -v gst-inspect-1.0 --exists v4l2slh264dec>/dev/null; then
	echo "v4l2slh264dec element is missing. Skipping the test"
	test-result h26forge-debian --result skip
	exit 0
fi

if [ ! -d /opt/h26forge/test_videos/ ]; then
	echo "bitstreams test directory missing. Skipping the test"
	test-result h26forge-debian --result skip
	exit 0
fi

cd /opt/h26forge/test_videos/

for i in $(seq -f "%04g" 0 99); do
	if command -v gst-launch-1.0 filesrc location=video$i.264.mp4 ! parsebin ! v4l2slh264dec ! fakesink>/dev/null; then
		test-result h26forge-debian --result fail
		exit 1
	fi
done

test-result h26forge-debian --result pass

exit 0
