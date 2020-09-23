#!/bin/sh

modes=$*
ls -l /dev/rtc0
if [ $? -eq 0 ];then
	lava-test-case rtc-exist --result pass
	for mode in $modes; do
		for i in $(seq 1 10); do
			rtcwake -d rtc0 -m $mode -s 5
		if [ $? -eq 0 ] && result="pass" || result="fail" ;then
				lava-test-case rtcwake-$mode-$i --result $result
			fi
		done
	done
else
	lava-test-case rtc-exist --result fail
	echo "No real time clock found !"
fi
