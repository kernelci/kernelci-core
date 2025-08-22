#!/bin/sh

set -x

GCOV_RESET="/sys/kernel/debug/gcov/reset"
if [ -f ${GCOV_RESET} ]; then
    echo 1 > ${GCOV_RESET};
fi
