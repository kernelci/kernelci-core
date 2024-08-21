#!/bin/sh

set -e

ret=0

if [ "$KERNELCI_LAVA" = "y" ]; then
    alias test-result='lava-test-case'
else
    alias test-result='echo'
fi

for level in crit alert emerg; do
    dmesg --level=$level --notime -x -k > dmesg.$level
    if [ -s "dmesg.$level" ]; then
        res=fail
        ret=1
    else
        res=pass
    fi
    count=$(cat dmesg.$level | wc -l)
    cat dmesg.$level
    test-result \
        $level \
        --result $res \
        --measurement $count \
        --units lines
done

exit $ret
