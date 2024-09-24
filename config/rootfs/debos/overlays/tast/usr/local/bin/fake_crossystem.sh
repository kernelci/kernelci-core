#!/bin/bash

# Hack Tast expect ChromeOS' crossystem.
# Since some Tast tests are expected
# to be executed on Debian,
# we need to create a dummy crossystem.
# See: https://chromium.googlesource.com/chromiumos/platform/tast-tests/+/refs/heads/release-R124-15823.B/src/go.chromium.org/tast-tests/cros/local/bundlemain/main.go#94

if [ "$1" = "mainfw_type" ]; then
    echo -n "recovery"
else
    echo -n "unknown"
fi
