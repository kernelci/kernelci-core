#!/bin/sh

FILE_NAME=$1

set -x

GCDA=/sys/kernel/debug/gcov

# Act only if $GCDA does exist (as GCOV is definitely enabled)
if [ -d ${GCDA} ]; then
    TEMPDIR=$(mktemp -d)
    # Retrieve GCOV artifacts
    # Taken from https://www.kernel.org/doc/html/v6.12/dev-tools/gcov.html#appendix-b-gather-on-test-sh
    find $GCDA -type d -exec mkdir -p $TEMPDIR/\{\} \;
    find $GCDA -name '*.gcda' -exec sh -c 'cat < $0 > '$TEMPDIR'/$0' {} \;
    find $GCDA -name '*.gcno' -exec sh -c 'cp -d $0 '$TEMPDIR'/$0' {} \;
    tar czf "${FILE_NAME}" -C $TEMPDIR sys
    rm -rf $TEMPDIR
fi
