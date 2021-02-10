#!/bin/sh

modes=$*

if [ -e /dev/rtc0 ]; then
    lava-test-case rtc-exist --result pass
else
    lava-test-case rtc-exist --result fail
    echo "No real-time clock found"
    exit 1
fi

if [ $(cat /sys/class/rtc/rtc0/device/power/wakeup) = enabled ]; then
    lava-test-case rtc-wakeup-enabled --result pass
else
    lava-test-case rtc-wakeup-enabled --result fail
    echo "Real-time clock wakeup not enabled"
    exit 1
fi

for mode in $modes; do
    for i in $(seq 1 10); do
	rtcwake -d rtc0 -m $mode -s 5
	if [ $? -eq 0 ] && result="pass" || result="fail" ;then
	    lava-test-case rtcwake-$mode-$i --result $result
	fi
    done
done

exit 0
