#!/bin/bash

# Important: This script is run under QEMU

set -e

# Build-depends needed to build the test suites, they'll be removed later
BUILD_DEPS="
            acl \
            acl-dev \
            attr \
            autoconf \
            automake \
            ca-certificates \
            gawk \
            git \
            gcc \
            libaio1 \
            libc6-dev \
            libcap2 \
            make \
            openssl \
            zip \
"

apt-get install --no-install-recommends -y  ${BUILD_DEPS}

BUILDFILE=/build_info.txt
echo '  "tests_suites": [' >> $BUILDFILE

# Build and install IO performance suites
########################################################################
TMP_TEST_DIR="/tmp/tests/clone"
mkdir -p ${TMP_TEST_DIR} && cd ${TMP_TEST_DIR}

TESTDIR=ltp
TEST_REPO=https://github.com/linux-test-project/ltp.git

git clone --depth=1 -b 20190115 ${TEST_REPO}
cd ${TESTDIR}

echo '    {"name": "${TESTDIR}", "git_url": "${TEST_REPO}", "git_commit": ' \"`git rev-parse HEAD`\" '}' >> $BUILDFILE

make autotools
./configure --prefix=/opt/ltp
make V=1
make V=1 install

find /opt/ltp/ -executable -type f -exec strip {} \;

echo '  ]' >> $BUILDFILE

########################################################################
# Cleanup: remove files and packages we don't want in the images       #
########################################################################
rm -rf ${TMP_TEST_DIR}

apt-get remove --purge -y ${BUILD_DEPS}
apt-get autoremove --purge -y
apt-get clean

# re-add some stuff that is removed by accident
apt-get install -y initramfs-tools

