#!/bin/bash

# Get first camera name
get_cam_name() {
	LIBCAMERA_LOG_LEVELS=FATAL lc-compliance | while read -r line; do
		echo "$line" | grep -qe '^- .*' && {
			cam_name=$(echo "$line" | sed 's/^- \(.*\)/\1/')
			echo "$cam_name"
			break
		}
	done
}

lc-compliance -c "$(get_cam_name)" | while read line; do

	echo "$line"

	# Look for a test
	echo "$line" | grep -qe '^\[ RUN      \]' && {

		test_set=$(echo "$line" | sed 's/^\[ RUN      \] \([^.]*\).*/\1/')

		test_case=$(echo "$line" | sed 's/^\[ RUN      \] [^.]*\.\(.*\)/\1/')

		[ "$test_set" != "$prev_test_set" ] && {
			[ -n "$prev_test_set" ] && lava-test-set stop
			lava-test-set start $test_set
			prev_test_set="$test_set"
		}

		continue
	}

	# Check for test result
	echo "$line" | grep -qe '^\[       OK \]' && res=pass
	echo "$line" | grep -qe '^\[  SKIPPED \]' && res=skip
	echo "$line" | grep -qe '^\[  FAILED  \]' && res=fail
	[ -n "$res" ] && lava-test-case "$test_case" --result "$res"

	res=''

	# End
	echo "$line" | grep -qe '^\[==========\]' && [ -n "$test_set" ] && {
		lava-test-set stop
		break
	}

done

exit 0
