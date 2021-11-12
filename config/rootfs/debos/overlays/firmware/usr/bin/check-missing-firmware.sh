#!/bin/sh

lava-test-set start no-missing-firmware

ignore_regex="maxtouch\.cfg|rockchip/dptx\.bin"

dmesg -l alert,crit,err,warn | grep firmware | grep -Ev "$ignore_regex" \
	&& lava-test-case no-missing-firmware --result fail \
	|| lava-test-case no-missing-firmware --result pass

lava-test-set stop
