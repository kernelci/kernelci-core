#!/bin/bash

#####################################################
# This script performs xfstests build
#####################################################

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    xfslibs-dev \
    uuid-dev \
    libacl1-dev \
    libaio-dev \
    libattr1-dev \
    git \
    automake \
    gcc \
    make \
    libtool-bin \
"
apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILDFILE=/test_suites.json
echo '{  "tests_suites": [' >> $BUILDFILE
XFSTESTS_URL=git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git
git clone --depth=1 $XFSTESTS_URL /xfstests && cd /xfstests

echo '    {"name": "xfstests", "git_url": "'$XFSTESTS_URL'", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE
echo '  ]}' >> $BUILDFILE

# Setup xfstests accounts, directory
useradd fsgqa -m
useradd 123456-fsgqa

mkdir /test /scratch

# Build xfstests
cd /xfstests && make && make install

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
apt-get remove --purge --allow-remove-essential -y  ${BUILD_DEPS}
