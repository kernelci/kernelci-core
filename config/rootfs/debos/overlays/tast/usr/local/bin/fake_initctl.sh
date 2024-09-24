#!/bin/bash

# Hack Tast expect chromeos' initctl.
# Since some Tast tests are expected to be executed on Debian,
# we need to create a dummy initctl

cmd="$1"
shift

case "$cmd" in
    stop)
        # Simulate stopping the job
        exit 0
        ;;
    status)
        jobname="$1"
        # Output the expected status
        echo "$jobname stop/waiting"
        exit 0
        ;;
    *)
        echo "initctl: Unknown command '$cmd'"
        exit 1
        ;;
esac
