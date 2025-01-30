#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="\
    fio \
    gcc \
    g++ \
    make
"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install --no-install-recommends -y ${BUILD_DEPS}

# Configure git
git config --global user.email "bot@kernelci.org"
git config --global user.name "KernelCI Bot"

########################################################################
# Build blktest                                                        #
########################################################################
BLKTEST_URL=https://github.com/osandov/blktests.git
mkdir -p /var/tests/blktest && cd /var/tests/blktest

git clone --depth 1 $BLKTEST_URL .

make
make install

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf /var/tests

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean
