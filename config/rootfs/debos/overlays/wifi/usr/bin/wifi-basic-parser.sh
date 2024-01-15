#!/bin/sh
#
# Copyright (C) 2024 Collabora Limited
# Author: Laura Nao <laura.nao@collabora.com>
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

# Check if rfkill is available
if ! command -v rfkill >/dev/null; then
    echo "rfkill not found. Please install it to proceed."
    exit 1
fi

# Check if iw is available
if ! command -v iw >/dev/null; then
    echo "iw could not be found. Please install it to proceed."
    exit 1
fi

# Check if iproute2 is available
if ! command -v ip >/dev/null; then
    echo "iproute2 could not be found. Please install it to proceed."
    exit 1
fi

# Find wlan interface name
wlan_if=$(iw dev | grep Interface | awk '{print $2}')

if [ -z "$wlan_if" ]; then
    echo "No wlan interface found."
    lava-test-case wlan-present --result fail
    exit 1
else
    echo "wlan interfaces found:"
    echo "$wlan_if"
    lava-test-case wlan-present --result pass
fi

lava-test-set start wlan-rfkill

# Check wlan rfkill presence
if rfkill --noheadings --raw --output ID,TYPE | grep wlan; then
    test-result rfkill-wlan-present --result pass
    # Check for hard-block
    if [ "$(rfkill --noheadings --raw --output ID,TYPE,SOFT,HARD | grep wlan | cut -d' ' -f4)" = "blocked" ]; then
        test-exception "wlan is hard-blocked"
        exit 1
    fi
    # Test soft block
    rfkill block wlan
    [ "$(rfkill --noheadings --raw --output ID,TYPE,SOFT | grep wlan | cut -d' ' -f3)" = "blocked" ] && res=pass || res=fail
    test-result rfkill-wlan-soft-block --result "$res"
    # Test soft unblock
    rfkill unblock wlan
    [ "$(rfkill --noheadings --raw --output ID,TYPE,SOFT | grep wlan | cut -d' ' -f3)" = "unblocked" ] && res=pass || res=fail
    test-result rfkill-wlan-soft-unblock --result "$res"
else
    test-result rfkill-wlan-present --result fail
    test-result rfkill-wlan-soft-block --result skip
    test-result rfkill-wlan-soft-unblock --result skip
fi

lava-test-set stop wlan-rfkill
lava-test-set start wlan-scan

# Bring interface up
ip link set "$wlan_if" up
while ! ip link show up | grep -q "$wlan_if"; do
    echo "Waiting for ${wlan_if} to come up"
    sleep 1
done

# Perform scan; assuming networks within reach
wlan_scan_results=$(iw dev "$wlan_if" scan)
if [ -n "$wlan_scan_results" ]; then
    wlan_scan_networks=$(echo "$wlan_scan_results" | grep -c 'ssid\|signal\|^bss')
    test-result wlan-scan --result pass --measurement "$wlan_scan_networks" --units networks
else
    test-result wlan-scan --result fail
fi

lava-test-set stop wlan-scan
lava-test-set start wlan-monitor

# Check if monitor mode is supported
if ! iw list | grep '\* monitor' >/dev/null; then
    echo "Monitor mode not supported."
    test-result wlan-monitor --result skip
else
    # Bring interface down
    ip link set "$wlan_if" down
    iw "$wlan_if" set monitor none
    ip link set "$wlan_if" up

    # Check monitor mode is active
    wlan_mode=$(iw dev "$wlan_if" info | grep type | awk '{print $2}')
    echo "${wlan_if} is in ${wlan_mode} mode"
    [ "$wlan_mode" = "monitor" ] && res=pass || res=fail
    test-result wlan-monitor-mode --result "$res"

    # Restore managed mode
    ip link set "$wlan_if" down
    iw "$wlan_if" set type managed
    ip link set "$wlan_if" up

    # Check managed mode has been restored
    wlan_mode=$(iw dev "$wlan_if" info | grep type | awk '{print $2}')
    echo "${wlan_if} is in ${wlan_mode} mode"
    [ "$wlan_mode" = "managed" ] && res=pass || res=fail
    test-result wlan-managed-mode --result "$res"
fi

lava-test-set stop wlan-monitor

exit 0
