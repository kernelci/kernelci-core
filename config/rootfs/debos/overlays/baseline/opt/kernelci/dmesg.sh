#!/bin/sh

set -e

if [ "$KERNELCI_LAVA" = "y" ]; then
    alias test-result='lava-test-case'
else
    alias test-result='echo'
fi

for level in crit alert emerg; do
    ${cmdwrapper} dmesg --level=$level --notime -x -k > dmesg.$level
    test -s dmesg.$level && res=fail || res=pass
    count=$(cat dmesg.$level | wc -l)
    cat dmesg.$level
    test-result \
        $level \
        --result $res \
        --measurement $count \
        --units lines
done

exit 0
